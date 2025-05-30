

from datetime import datetime, timedelta, timezone
import logging

from sqlmodel import select

from app.configuration.settings import Configuration
from app.enums.cart import CartStatus
from app.models.cart import Cart
from app.database.connection import get_session

Configuration()

def expire_old_carts():
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=7)

    with get_session() as session:
        carts = session.exec(
            select(Cart).where(
                Cart.status == CartStatus.ACTIVE,
                Cart.updated_at < threshold
            )
        ).all()

        for cart in carts:
            cart.status = CartStatus.EXPIRED
            cart.updated_at = now

        session.commit()
        logging.info(f"Apagando {len(carts)} carrinhos expirados")
        
def delete_expired_carts():
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(days=30)

    with get_session() as session:
        carts = session.exec(
            select(Cart).where(
                Cart.status == CartStatus.EXPIRED,
                Cart.updated_at < threshold
            )
        ).all()

        for cart in carts:
            session.delete(cart)

        session.commit()
        logging.info(f"Apagando {len(carts)} carrinhos expirados permanentemente")

