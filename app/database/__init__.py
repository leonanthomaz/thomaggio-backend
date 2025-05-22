# app/database/__init__.py

from .connection import get_session
from .populate import populate_database

def init_db():
    """Inicializa o banco de dados e popula com dados iniciais."""
    session = get_session()
    populate_database(session)
