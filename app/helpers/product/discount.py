from datetime import datetime, timezone
import logging
from sqlmodel import select
from app.configuration.settings import Configuration
from app.models.product.product import Product
from app.database.connection import get_session

Configuration()

def clear_expired_promotions():
    now = datetime.now(timezone.utc)
    
    with get_session() as session:
        statement = select(Product).where(Product.promotion_end_at < now)
        products = session.exec(statement).all()

        for product in products:
            product.promotion_discount_percentage = None
            product.promotion_start_at = None
            product.promotion_end_at = None
            product.updated_at = now
            session.add(product)

        session.commit()

        logging.info(f"PROMOÇÃO >>> Limpeza de promoções expiradas concluída. {len(products)} produtos atualizados.")
