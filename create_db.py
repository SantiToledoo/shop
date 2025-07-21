from app import create_app, db
from app.models import pedidos, item_pedido  # Asegurate que esto importe los modelos

app = create_app()

with app.app_context():
    db.create_all()
    print("Tablas creadas.")
