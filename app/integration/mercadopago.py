from app.configuration.settings import Configuration
import mercadopago
from mercadopago.config.request_options import RequestOptions

configuration = Configuration()

if configuration.environment == "production":
    sdk = mercadopago.SDK(configuration.mercado_pago_access_token_prod)
else:
    request_options = RequestOptions()
    request_options.sandbox = True

    sdk = mercadopago.SDK(
        access_token=configuration.mercado_pago_access_token_test,
        request_options=request_options
    )
