import mercadopago
from app.configuration.settings import Configuration

configuration = Configuration()
sdk = mercadopago.SDK(configuration.mercado_pago_access_token_test)
