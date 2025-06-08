import logging
import os
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carrega as variáveis de ambiente
load_dotenv(dotenv_path=".env", encoding="utf-8")

# Silencia logs de SQLAlchemy
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

class Configuration:
    def __init__(self):
        
        # Url base
        self.base_url = os.getenv("BASE_URL", "http://localhost:3000")
        
        # Configurações do ambiente e banco de dados
        self.environment = os.getenv("ENVIRONMENT", "development").lower()
        
        self.jwt_expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
        
        # Email
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        # POSTGRES PRODUCTION
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME")
        
        # POSTGRES
        self.db_dev_user = os.getenv("DB_DEV_USER")
        self.db_dev_password = os.getenv("DB_DEV_PASSWORD")
        self.db_dev_host = os.getenv("DB_DEV_HOST")
        self.db_dev_port = os.getenv("DB_DEV_PORT", "5432")
        self.db_dev_name = os.getenv("DB_DEV_NAME")
        
        self.endpoint_url_r2 = os.getenv("ENDPOINT_CLOUDFLARE_R2")
        self.aws_access_key_id_aws = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key_aws = os.getenv("AWS_SECRET_ACCESS_KEY_ID")
        self.r2_bucket_name = os.getenv("R2_BUCKET_NAME")
        self.r2_url_public = os.getenv("ENDPOINT_PUBLIC_R2")
        
        self.mercado_pago_key_test = os.getenv("MERCADO_PAGO_PUBLIC_KEY_TEST")
        self.mercado_pago_access_token_test = os.getenv("MERCADO_PAGO_ACCESS_TOKEN_TEST")
        self.mercado_pago_access_token_prod = os.getenv("MERCADO_PAGO_ACCESS_TOKEN_PROD")
                    

    def connect_to_postgresql(self):
        # Montar a URL de conexão corretamente
        db_url = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        logging.info(f"BANCO DE DADOS >>> SELECIONADO DE PRODUÇÃO -> : {db_url}")
        return db_url
    
    def connect_to_postgresql_dev(self):
        # Montar a URL de conexão corretamente
        db_url = f"postgresql://{self.db_dev_user}:{self.db_dev_password}@{self.db_dev_host}:{self.db_dev_port}/{self.db_dev_name}"
        logging.info(f"BANCO DE DADOS >>> SELECIONADO DE DESENVOLVIMENTO -> : {db_url}")
        return db_url
    