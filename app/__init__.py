# app/__init__.py
from flask import Flask
from app.db import db
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

# Instancias globales
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'santiago1234'

    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../Instance/olistica.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Rutas protegidas redirigen al login
    login_manager.login_view = 'auth.login'

    # Cargar usuario para Flask-Login
    from app.models.usuario import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    # Registrar blueprints después de que todo esté inicializado
    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.auth import auth

    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(auth)

    return app
