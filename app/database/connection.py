# app/database/connection.py

import logging
from sqlmodel import create_engine, SQLModel, Session
from app.configuration.settings import Configuration

# Configuração global já carregada
configuration = Configuration()

def get_session():
    """Cria e retorna a sessão para interação com o banco de dados."""
    try:
        if configuration.environment == "development":
            db_url = configuration.connect_to_postgresql_dev()
        else:
            db_url = configuration.connect_to_postgresql()
            
        # Criação do engine para a conexão com o banco de dados
        engine = create_engine(db_url, echo=False)

        # Criando as tabelas no banco de dados (caso não existam)
        SQLModel.metadata.create_all(bind=engine)

        # Criação da sessão
        session = Session(engine)
        return session
    except Exception as e:
        logging.error(f"Erro ao conectar ao banco de dados: {e}")
        raise
