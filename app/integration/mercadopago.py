from app.configuration.settings import Configuration
import mercadopago
from mercadopago.config.request_options import RequestOptions

configuration = Configuration()

# Configuração única para todos os ambientes
request_options = RequestOptions()

if configuration.environment == "production":
    sdk = mercadopago.SDK(
        access_token=configuration.mercado_pago_access_token_prod,
        request_options=request_options
    )
else:
    # Configuração específica para sandbox
    request_options.access_token = configuration.mercado_pago_access_token_test
    request_options.custom_headers = {"x-test-scope": "sandbox"}
    
    sdk = mercadopago.SDK(
        access_token=configuration.mercado_pago_access_token_test,
        request_options=request_options
    )