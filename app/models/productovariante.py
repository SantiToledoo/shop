from app.db import db

class ProductoVariante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # "talle" o "color"
    valor = db.Column(db.String(50), nullable=False)

    producto = db.relationship("Producto", backref=db.backref("variantes", lazy=True))
