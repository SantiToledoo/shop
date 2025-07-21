from app import create_app, db, bcrypt
from app.models.usuario import Usuario

app = create_app()

with app.app_context():
    username = 'admin'
    password = 'admin123'
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    if not Usuario.query.filter_by(username=username).first():
        nuevo = Usuario(username=username, password=hashed_password)
        db.session.add(nuevo)
        db.session.commit()
        print("Usuario admin creado.")
    else:
        print("El usuario ya existe.")
