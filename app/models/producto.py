from app.db import db

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    precio = db.Column(db.Float, nullable=False)
    imagen_url = db.Column(db.String(255))
    stock = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Producto {self.nombre}>'