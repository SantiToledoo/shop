from faker import Faker
import random

from app import create_app
from app.db import db
from app.models import Producto

fake = Faker()

# Creamos la app desde la factory
app = create_app()

with app.app_context():
    for _ in range(30):
        producto = Producto(
            nombre=fake.word().capitalize(),
            descripcion=fake.sentence(nb_words=5),
            precio=round(random.uniform(100, 5000), 2),
            stock=random.randint(0, 100),
            imagen_url="/static/img/default.jpg"
        )
        db.session.add(producto)

    db.session.commit()
    print("✅ 30 productos falsos cargados correctamente.")
