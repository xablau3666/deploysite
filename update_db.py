from app import app, db
from models import Usuario, Produto

with app.app_context():
    db.drop_all() 
    db.create_all()
    print("Banco de dados atualizado com sucesso!")
