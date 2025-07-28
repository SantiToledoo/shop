# app/routes/admin.py
from flask import render_template, request, redirect, url_for,session
from flask import Blueprint
import os
from werkzeug.utils import secure_filename
from flask import flash
from flask_login import login_required, current_user
from app.models.producto import Producto
from app.models.pedidos import Pedido
from app.models.item_pedido import ItemPedido


admin = Blueprint('admin', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'img')

@admin.route('/admin/productos', methods=['GET', 'POST'])
@login_required
def cargar_producto():
    from app import db
    from app.models.producto import Producto

    if request.method == 'POST':
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        precio = request.form['precio']
        stock = request.form['stock']
        imagen = request.files['imagen']

        if not nombre or not descripcion or not precio or not stock or not imagen:
            flash('Todos los campos son obligatorios.', 'error')
            return redirect(url_for('admin.cargar_producto'))
        
        try:
            precio = float(precio)
            if precio <= 0:
                flash('El precio debe ser mayor a 0.', 'error')
                return redirect(url_for('admin.cargar_producto'))
        except ValueError:
            flash('El precio debe ser un número válido.', 'error')
            return redirect(url_for('admin.cargar_producto'))

        try:
            stock = int(stock)
            if stock < 0:
                flash('El stock no puede ser negativo.', 'error')
                return redirect(url_for('admin.cargar_producto'))
        except ValueError:
            flash('El stock debe ser un número entero.', 'error')
            return redirect(url_for('admin.cargar_producto'))

        filename = secure_filename(imagen.filename)
        imagen_path = os.path.join(UPLOAD_FOLDER, filename)
        imagen.save(imagen_path)

        imagen_url = f'/static/img/{filename}'

        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=float(precio),
            imagen_url=imagen_url,
            stock=int(stock)
        )

        db.session.add(nuevo_producto)
        db.session.commit()
        flash('Producto creado con éxito.', 'success')
        return redirect(url_for('admin.listar_productos'))

    return render_template('admin/cargar_producto.html')


@admin.route('/admin/productos/listar')
@login_required
def listar_productos():
    from app import db
    from app.models.producto import Producto
    productos = Producto.query.all()
    return render_template('admin/listar_productos.html', productos=productos)

@admin.route('/admin/productos/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_producto(id):
    from app import db
    from app.models.producto import Producto

    producto = Producto.query.get_or_404(id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        db.session.commit()
        flash('Producto editado con éxito.', 'success')
        return redirect(url_for('admin.listar_productos'))

    return render_template('admin/editar_producto.html', producto=producto)

@admin.route('/admin/productos/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar_producto(id):
    from app import db
    from app.models.producto import Producto

    producto = Producto.query.get_or_404(id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado con éxito.', 'success')
    return redirect(url_for('admin.listar_productos'))

@admin.route('/carrito/agregar/<int:producto_id>', methods=['POST'])
def agregar_al_carrito(producto_id):
    carrito = session.get('carrito', {})

    producto_id_str = str(producto_id)
    try:
        cantidad = int(request.form.get('cantidad', 1))
    except ValueError:
        cantidad = 1

    # Sumar a lo que ya haya
    carrito[producto_id_str] = carrito.get(producto_id_str, 0) + cantidad

    session['carrito'] = carrito
    flash(f'Se agregaron {cantidad} unidades al carrito', 'success')
    return redirect(url_for('main.index'))

@admin.route('/carrito/eliminar/<int:producto_id>', methods=['POST'])
def eliminar_del_carrito(producto_id):
    carrito = session.get('carrito', {})

    producto_id_str = str(producto_id)
    if producto_id_str in carrito:
        del carrito[producto_id_str]
        session['carrito'] = carrito
        flash('Producto eliminado del carrito.', 'success')
    else:
        flash('Producto no encontrado en el carrito.', 'error')

    return redirect(url_for('admin.ver_carrito'))


@admin.route('/carrito')
def ver_carrito():
    carrito = session.get('carrito', {})
    productos = []
    total = 0

    for producto_id_str, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id_str))
        if producto:
            subtotal = producto.precio * cantidad
            productos.append({
                'producto': producto,
                'cantidad': cantidad,
                'subtotal': subtotal
            })
            total += subtotal

    return render_template('carrito.html', productos=productos, total=total)

@admin.route('/carrito/confirmar', methods=['POST'])
def confirmar_compra():
    from app import db

    carrito = session.get('carrito', {})
    if not carrito:
        flash("El carrito está vacío.", "error")
        return redirect(url_for('admin.ver_carrito'))

    usuario_id = current_user.id if current_user.is_authenticated else None
    nuevo_pedido = Pedido(usuario_id=usuario_id, total=0)
    db.session.add(nuevo_pedido)
    db.session.flush()  # Para obtener el ID

    total_pedido = 0

    for producto_id_str, cantidad in carrito.items():
        producto = Producto.query.get(int(producto_id_str))
        if not producto:
            flash("Producto no encontrado.", "error")
            return redirect(url_for('admin.ver_carrito'))

        if producto.stock < cantidad:
            flash(f"No hay suficiente stock para {producto.nombre}.", "error")
            return redirect(url_for('admin.ver_carrito'))

        producto.stock -= cantidad
        subtotal = producto.precio * cantidad
        total_pedido += subtotal

        item = ItemPedido(
            pedido_id=nuevo_pedido.id,
            producto_id=producto.id,
            cantidad=cantidad
        )
        db.session.add(item)

    nuevo_pedido.total = total_pedido  # Guardás el total en el Pedido

    db.session.commit()
    session['carrito'] = {}
    flash("¡Pedido realizado con éxito!", "success")
    return redirect(url_for('main.index'))






@admin.route('/producto/<int:id>')
def detalle_producto(id):
    producto = Producto.query.get_or_404(id)
    similares = Producto.query.filter(Producto.id != id).limit(4).all()  # muestra 4 productos distintos
    return render_template('detalle_producto.html', producto=producto, similares=similares)

@admin.route('/admin/pedidos')
@login_required
def ver_pedidos():
    pedidos = Pedido.query.order_by(Pedido.id.desc()).all()
    return render_template('ver_pedidos.html', pedidos=pedidos)

@admin.route('/admin/pedidos/<int:pedido_id>/entregar', methods=['POST'])
@login_required
def marcar_entregado(pedido_id):
    from app import db
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.estado = 'Entregado'
    db.session.commit()
    return redirect(url_for('admin.ver_pedidos'))

@admin.route('/admin/pedidos/<int:pedido_id>/rechazar', methods=['POST'])
@login_required
def marcar_rechazado(pedido_id):
    from app import db
    pedido = Pedido.query.get_or_404(pedido_id)
    pedido.estado = 'Rechazado'
    db.session.commit()
    return redirect(url_for('admin.ver_pedidos'))
