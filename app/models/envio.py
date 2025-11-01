from app.db import db

class Envio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    localidad = db.Column(db.String(100), nullable=False)
    provincia = db.Column(db.String(100), nullable=False)
    codigo_postal = db.Column(db.String(10), nullable=False)
    telefono = db.Column(db.String(20))
    metodo_envio = db.Column(db.String(50), nullable=False)  # "domicilio" o "sucursal"
    costo_envio = db.Column(db.Float, default=0.0)

    pedido = db.relationship('Pedido', backref='envio', lazy=True)
