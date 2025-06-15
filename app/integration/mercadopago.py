from app.configuration.settings import Configuration
import mercadopago

configuration = Configuration()

if configuration.environment == "production":
    sdk = mercadopago.SDK(configuration.mercado_pago_access_token_prod)
else:
    sdk = mercadopago.SDK(configuration.mercado_pago_access_token_test)