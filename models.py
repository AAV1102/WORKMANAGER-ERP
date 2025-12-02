# flask-todo-app/models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

# Si ya tienes esta línea en tu proyecto, NO la copies de nuevo.
db = SQLAlchemy()

# --- AÑADE ESTA CLASE A TU ARCHIVO DE MODELOS ---
class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    serial = db.Column(db.String, unique=True, nullable=False, index=True)
    # ... (y todas las demás columnas que definimos antes)
    # Pega aquí el resto de las columnas de la clase InventoryItem del paso anterior
    # para mantener este bloque de código más corto.
    codigo_unificado = db.Column(db.String, index=True)
    codigo_individual = db.Column(db.String, unique=True, index=True)
    placa = db.Column(db.String)
    # ... (continúa con todas las demás)
    fecha_ultima_modificacion = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    archivo_origen = db.Column(db.String)
