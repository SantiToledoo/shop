from app.db import db
from datetime import datetime


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)  # antes era False
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(50), default='pendiente')
    motivo_rechazo = db.Column(db.String(255))
    total = db.Column(db.Float, nullable=False)

    items = db.relationship('ItemPedido', backref='pedido', lazy=True)

