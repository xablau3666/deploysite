from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db
from models import Produto, Usuario
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loja.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db.init_app(app)
bcrypt = Bcrypt(app)

@app.template_filter('currency')
def currency_format(value):
    return f'R$ {value:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    produtos = Produto.query.all()
    return render_template('index.html', produtos=produtos)

@app.route('/produto/<int:produto_id>')
def produto(produto_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    produto = Produto.query.get_or_404(produto_id)
    return render_template('produto.html', produto=produto)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    if 'usuario_id' not in session or not session.get('is_admin'):
        flash('Acesso negado. Somente administradores podem adicionar produtos.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        nome = request.form['nome']
        preco = request.form['preco'].replace('R$ ', '').replace('.', '').replace(',', '.')
        descricao = request.form['descricao']
        imagem = request.form['imagem']
        categoria = request.form['categoria']
        novo_produto = Produto(nome=nome, preco=float(preco), descricao=descricao, imagem=imagem, categoria=categoria)
        db.session.add(novo_produto)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('adicionar_produto.html')

@app.route('/remover/<int:produto_id>')
def remover_produto(produto_id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        flash('Acesso negado. Somente administradores podem remover produtos.')
        return redirect(url_for('index'))
    produto = Produto.query.get_or_404(produto_id)
    db.session.delete(produto)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/editar/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    if 'usuario_id' not in session or not session.get('is_admin'):
        flash('Acesso negado. Somente administradores podem editar produtos.')
        return redirect(url_for('index'))
    produto = Produto.query.get_or_404(produto_id)
    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.preco = request.form['preco'].replace('R$ ', '').replace('.', '').replace(',', '.')
        produto.descricao = request.form['descricao']
        produto.imagem = request.form['imagem']
        produto.categoria = request.form['categoria']
        db.session.commit()
        return redirect(url_for('index'))
    produto.preco = f'R$ {produto.preco:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return render_template('editar_produto.html', produto=produto)

@app.route('/categoria/<categoria>')
def categoria(categoria):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    produtos = Produto.query.filter_by(categoria=categoria).all()
    return render_template('index.html', produtos=produtos)

@app.route('/carrinho')
def carrinho():
    if 'carrinho' not in session:
        session['carrinho'] = []
    total = sum(item['preco'] for item in session['carrinho'])
    return render_template('carrinho.html', produtos=session['carrinho'], total=total)

@app.route('/adicionar_carrinho/<int:produto_id>')
def adicionar_carrinho(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    item = {
        'id': produto.id,
        'nome': produto.nome,
        'preco': produto.preco,
        'descricao': produto.descricao,
        'imagem': produto.imagem
    }
    if 'carrinho' not in session:
        session['carrinho'] = []
    session['carrinho'].append(item)
    session.modified = True
    flash(f'{produto.nome} adicionado ao carrinho.')
    return redirect(url_for('index'))

@app.route('/remover_carrinho/<int:produto_id>')
def remover_carrinho(produto_id):
    if 'carrinho' in session:
        session['carrinho'] = [item for item in session['carrinho'] if item['id'] != produto_id]
        session.modified = True
    return redirect(url_for('carrinho'))

@app.route('/checkout')
def checkout():
    total = sum(item['preco'] for item in session['carrinho'])
    return render_template('checkout.html', total=total)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and usuario.check_senha(senha):
            session['usuario_id'] = usuario.id
            session['is_admin'] = usuario.is_admin
            return redirect(url_for('index'))
        else:
            flash('Login ou senha incorretos')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        admin_senha = request.form.get('admin_senha')
        is_admin = False
        if request.form.get('is_admin') and admin_senha == '2024':
            is_admin = True
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            flash('Usuário já cadastrado com esse email')
            return redirect(url_for('register'))
        novo_usuario = Usuario(nome=nome, email=email, is_admin=is_admin)
        novo_usuario.set_senha(senha)
        db.session.add(novo_usuario)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
