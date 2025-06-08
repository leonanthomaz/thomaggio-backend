from datetime import datetime, timezone
import logging
from sqlmodel import select
from app.configuration.settings import Configuration
from app.enums.payment_status import PaymentStatus
from app.models.payment import Payment
from app.database.connection import get_session

Configuration()

def cancel_expired_payments():
    with get_session() as session:
        now = datetime.now(timezone.utc)

        expired_payments = session.exec(
            select(Payment).where(
                Payment.status == PaymentStatus.PENDING,
                Payment.expires_at.is_not(None),
                Payment.expires_at < now
            )
        ).all()

        for payment in expired_payments:
            # Se expires_at não tem tzinfo, coloca UTC
            expires_at = payment.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            time_diff = now - expires_at

            payment.status = PaymentStatus.CANCELED
            payment.qr_code_base64 = None
            payment.updated_at = now
            session.add(payment)
            logging.info(f"PAGAMENTO >>> Pagamento {payment.id} cancelado por expiração. Tempo desde expiração: {time_diff.total_seconds()} segundos.")

        session.commit() 
        logging.info(f"PAGAMENTO >>> Cancelamento de {len(expired_payments)} pagamentos expirados concluído.")