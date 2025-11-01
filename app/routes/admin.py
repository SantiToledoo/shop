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
from app.models.productovariante import ProductoVariante
import mercadopago


admin = Blueprint('admin', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'img')
# Inicializá el SDK con tu Access Token
sdk = mercadopago.SDK("APP_USR-2242152984017973-101211-f47713496164e7ae22a6df827bbd9e75-2919985747")

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

        talle = request.form.get('talle') or None
        color = request.form.get('color') or None

        if not nombre or not descripcion or not precio or not stock or not imagen:
            flash('Todos los campos obligatorios deben completarse.', 'error')
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

        usa_talle = 'usa_talle' in request.form
        usa_color = 'usa_color' in request.form

        nuevo_producto = Producto(
            nombre=nombre,
            descripcion=descripcion,
            precio=float(precio),
            imagen_url=imagen_url,
            stock=int(stock)
        )
        db.session.add(nuevo_producto)
        db.session.commit()

        # Guardar talles
        if 'usa_talle' in request.form:
            talles = request.form.getlist('talles[]')
            for talle in talles:
                if talle.strip():
                    db.session.add(ProductoVariante(producto_id=nuevo_producto.id, tipo="talle", valor=talle.strip()))

        # Guardar colores
        if 'usa_color' in request.form:
            colores = request.form.getlist('colores[]')
            for color in colores:
                if color.strip():
                    db.session.add(ProductoVariante(producto_id=nuevo_producto.id, tipo="color", valor=color.strip()))

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
    pid = str(producto_id)

    cantidad = int(request.form.get('cantidad', 1))
    talle = request.form.get('talle')
    color = request.form.get('color')

    if pid not in carrito:
        carrito[pid] = []

    # Si ya existe la misma variante (talle + color), sumamos cantidad
    for item in carrito[pid]:
        if item.get('talle') == talle and item.get('color') == color:
            item['cantidad'] += cantidad
            break
    else:
        carrito[pid].append({"cantidad": cantidad, "talle": talle, "color": color})

    session['carrito'] = carrito
    flash(f'Se agregaron {cantidad} unidades al carrito', 'success')
    return redirect(url_for('main.index'))


@admin.route('/carrito/eliminar/<int:producto_id>/<int:idx>', methods=['POST'])
def eliminar_del_carrito(producto_id, idx):
    carrito = session.get('carrito', {})
    pid = str(producto_id)

    if pid in carrito and 0 <= idx < len(carrito[pid]):
        carrito[pid].pop(idx)
        if not carrito[pid]:
            del carrito[pid]
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

    for producto_id_str, items in carrito.items():
        producto = Producto.query.get(int(producto_id_str))
        if producto:
            for idx, item in enumerate(items):
                cantidad = item['cantidad']
                talle = item.get('talle', '-') or '-'
                color = item.get('color', '-') or '-'
                subtotal = producto.precio * cantidad
                productos.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'talle': talle,
                    'color': color,
                    'subtotal': subtotal,
                    'variante_index': idx
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

    for producto_id_str, items in carrito.items():
        producto = Producto.query.get(int(producto_id_str))
        if not producto:
            flash("Producto no encontrado.", "error")
            return redirect(url_for('admin.ver_carrito'))

        for item in items:  # iteramos cada variante
            cantidad = item['cantidad']
            talle = item.get('talle', '-') or '-'
            color = item.get('color', '-') or '-'

            if producto.stock < cantidad:
                flash(f"No hay suficiente stock para {producto.nombre} ({talle}, {color}).", "error")
                return redirect(url_for('admin.ver_carrito'))

            producto.stock -= cantidad
            subtotal = producto.precio * cantidad
            total_pedido += subtotal

            item_pedido = ItemPedido(
                pedido_id=nuevo_pedido.id,
                producto_id=producto.id,
                cantidad=cantidad,
                # talle=talle,  # si agregás columna talle
                # color=color   # si agregás columna color
            )
            db.session.add(item_pedido)

    envio_data = session.get('envio')
    if envio_data:
        envio = envio(pedido_id=nuevo_pedido.id, **envio_data)
        db.session.add(envio)
        total_pedido += envio_data['costo_envio']

    nuevo_pedido.total = total_pedido
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

    # Restaurar el stock de cada producto
    for item in pedido.items:
        producto = Producto.query.get(item.producto_id)
        if producto:
            producto.stock += item.cantidad

    pedido.estado = 'Rechazado'
    db.session.commit()

    flash("Pedido rechazado y stock restaurado correctamente.", "success")
    return redirect(url_for('admin.ver_pedidos'))


@admin.route('/pagar_mercado_pago', methods=['POST'])
def pagar_mercado_pago():
    total = request.form['total']

    preference_data = {
        "items": [
            {
                "title": "Compra en tu tienda",
                "quantity": 1,
                "unit_price": float(total)
            }
        ],
        "back_urls": {
            "success": "http://localhost:5000/pago_exitoso",
            "failure": "http://localhost:5000/pago_fallido",
            "pending": "http://localhost:5000/pago_pendiente"
        }
    
    }


    # Usar el link de sandbox para pruebas
    preference_response = sdk.preference().create(preference_data)
    print("🔍 Respuesta de Mercado Pago:", preference_response)

    response_data = preference_response.get("response", {})

    link_de_pago = response_data.get("sandbox_init_point") or response_data.get("init_point")

    if link_de_pago:
        return redirect(link_de_pago)
    else:
        flash("Hubo un problema al generar el link de pago.", "danger")
        return redirect(url_for('admin.ver_carrito'))




@admin.route('/pagar_transferencia', methods=['POST'])
def pagar_transferencia():
    total = request.form['total']
    flash('Datos para transferencia: CBU 000000000000000000001, Alias: TUEMPRESA.PAGO', 'info')
    return redirect(url_for('admin.ver_carrito'))


@admin.route('/pagar_en_local', methods=['POST'])
def pagar_en_local():
    flash('Podés pasar por el local a retirar y pagar. Dirección: Calle Falsa 123, San Miguel.', 'info')
    return redirect(url_for('admin.ver_carrito'))



@admin.route('/pago_exitoso')
def pago_exitoso():
    flash("¡Pago aprobado! Gracias por tu compra.", "success")
    return redirect(url_for('admin.ver_carrito'))


@admin.route('/pago_fallido')
def pago_fallido():
    flash("Hubo un problema con el pago. Intentá nuevamente.", "danger")
    return redirect(url_for('admin.ver_carrito'))


@admin.route('/pago_pendiente')
def pago_pendiente():
    flash("Tu pago está pendiente. Te avisaremos cuando se confirme.", "warning")
    return redirect(url_for('admin.ver_carrito'))

@admin.route('/envio', methods=['GET', 'POST'])
def confirmar_envio():
    from app import db

    if request.method == 'POST':
        datos_envio = {
            "nombre": request.form['nombre'],
            "direccion": request.form['direccion'],
            "localidad": request.form['localidad'],
            "provincia": request.form['provincia'],
            "codigo_postal": request.form['codigo_postal'],
            "telefono": request.form.get('telefono'),
            "metodo_envio": request.form['metodo_envio'],
            "costo_envio": float(request.form['costo_envio'])
        }

        session['envio'] = datos_envio  # lo guardamos para usar al confirmar pedido

        flash("Datos de envío guardados. Ahora podés continuar con el pago.", "success")
        return redirect(url_for('admin.ver_carrito'))  # o al checkout

    return render_template('envio.html')

