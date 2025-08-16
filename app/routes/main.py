# app/routes/main.py
from flask import Blueprint, render_template,session,redirect,render_template, request, url_for,flash
from app.models.producto import Producto
from flask import flash


main = Blueprint('main', __name__)

@main.route('/')
def index():
    # Obtener todos los productos desde la base de datos
    productos = Producto.query.all()

    # Pasar los productos al template
    return render_template('index.html', productos=productos)
