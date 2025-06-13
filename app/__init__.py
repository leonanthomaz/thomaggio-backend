import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.configuration.settings import Configuration
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.helpers.scheduler.scheduler import start_scheduler

from app.auth.auth import AuthRouter
from app.admin.admin import AdminRouter

from app.routes.company.home import HomeRouter

from app.routes.user.address import AddressRouter
from app.routes.company.company import CompanyRouter
from app.routes.user.user import UserRouter
from app.routes.product.product import ProductRouter
from app.routes.product.category import CategoryRouter
from app.routes.chat.chat import WhatsAppRouter
from app.routes.cart.cart import CartRouter
from app.routes.order.order import OrderRouter
from app.routes.supply.supply import SupplyRouter
from app.routes.supply.product_supply import ProductSupplyRouter
from app.routes.company.delivery import DeliveryRouter
from app.routes.chat.token_status import TokenStatusRouter
from app.routes.payment.payment import PaymentRouter
from app.routes.company.promocode import PromoCodeRouter

from app.tasks.websockets import routes as websocket_routes

configuration = Configuration()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info(f"SISTEMA >>> Ambiente carregado: {configuration.environment}")

def create_app():
    """
    Cria e configura a aplicação FastAPI, incluindo middlewares e rotas.
    """
    app = FastAPI()

    logging.info("SISTEMA >>> Inicializando o banco de dados...")
    init_db()
    start_scheduler()

    origins = ["http://localhost:3000", "http://localhost:3001"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Configure a montagem dos arquivos estáticos AQUI
    app.mount("/static", StaticFiles(directory="assets"), name="static")
    logging.info("SISTEMA >>> Rota /static montada para servir arquivos estáticos de assets")
        
    app.include_router(HomeRouter())

    app.include_router(AuthRouter())
    app.include_router(AdminRouter())

    app.include_router(AddressRouter())
    app.include_router(CompanyRouter())
    app.include_router(UserRouter())
    app.include_router(ProductRouter())
    app.include_router(CategoryRouter())
    app.include_router(CartRouter())
    app.include_router(OrderRouter())
    app.include_router(SupplyRouter())
    app.include_router(ProductSupplyRouter())
    app.include_router(DeliveryRouter())
    app.include_router(TokenStatusRouter())
    app.include_router(PaymentRouter())
    app.include_router(PromoCodeRouter())
    app.include_router(WhatsAppRouter())

    app.include_router(websocket_routes.router)

    return app
