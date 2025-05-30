import logging
from fastapi import FastAPI
from app.configuration.settings import Configuration
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.functions.scheduler.scheduler import start_scheduler

from app.auth.auth import AuthRouter
from app.admin.users import AdminRouter

from app.routes.home import HomeRouter

from app.routes.company import CompanyRouter
from app.routes.user import UserRouter
from app.routes.product import ProductRouter
from app.routes.category import CategoryRouter
from app.routes.cart import CartRouter
from app.routes.order import OrderRouter
from app.routes.supply import SupplyRouter
from app.routes.product_supply import ProductSupplyRouter
from app.routes.delivery import DeliveryRouter
from app.routes.token_status import TokenStatusRouter
from app.routes.payment import PaymentRouter

from app.websockets import routes as websocket_routes

configuration = Configuration()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info(f"Ambiente carregado: {configuration.environment}")

def create_app():
    """
    Cria e configura a aplicação FastAPI, incluindo middlewares e rotas.
    """
    app = FastAPI()

    logging.info("Inicializando o banco de dados...")
    init_db()
    start_scheduler()

    origins = ["https://thomaggio.vercel.app", "https://thomaggio-dashboard.vercel.app"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(HomeRouter())

    app.include_router(AuthRouter())
    app.include_router(AdminRouter())

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

    app.include_router(websocket_routes.router)

    return app
