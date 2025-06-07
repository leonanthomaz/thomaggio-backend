import mercadopago
from app.configuration.settings import Configuration

configuration = Configuration()
if configuration.environment == "production":
    sdk = mercadopago.SDK(configuration.mercado_pago_access_token_prod)
else:
    sdk = mercadopago.SDK(configuration.mercado_pago_access_token_test)

