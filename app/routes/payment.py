from datetime import datetime, timedelta, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.configuration.settings import Configuration
from app.database.connection import get_session
from app.auth.auth import AuthRouter
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import PaymentRequest, PaymentResponse
from app.enums.payment_status import PaymentStatus
from app.api.mercadopago import sdk

Configuration()
db_session = get_session
get_current_user = AuthRouter().get_current_user


class PaymentRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/payment/", self.create_payment, methods=["POST"], response_model=PaymentResponse)
        self.add_api_route("/payment/pix-qrcode", self.generate_pix_qrcode, methods=["POST"])
        self.add_api_route("/payment/webhook", self.handle_webhook, methods=["POST"])
        self.add_api_route("/payment/{order_code}", self.get_payment, methods=["GET"], response_model=PaymentResponse)

    def create_payment(self, data: PaymentRequest, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.id == data.order_id)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")
            
            expiration_time = datetime.now(timezone.utc) + timedelta(minutes=5)

            payment = Payment(
                order_id=data.order_id,
                method=data.method,
                amount=data.amount,
                status=PaymentStatus.PENDING,
                expires_at=expiration_time
            )

            session.add(payment)
            session.commit()
            session.refresh(payment)
            return payment
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def get_payment(self, order_code: str, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.code == order_code)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")

            payment = session.exec(select(Payment).where(Payment.order_id == order.id)).first()
            if not payment:
                raise HTTPException(status_code=404, detail="Pagamento não encontrado")

            return payment
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def make_aware(self, dt: datetime) -> datetime:
        """Garante que o datetime é timezone-aware (UTC)."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    def generate_pix_qrcode(self, data: PaymentRequest, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.id == data.order_id)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")

            # Verifica se já existe pagamento pendente
            existing_payment = session.exec(
                select(Payment).where(
                    Payment.order_id == data.order_id,
                    Payment.status == PaymentStatus.PENDING,
                    Payment.method == "pix"
                )
            ).first()

            now_utc = datetime.now(timezone.utc)

            if existing_payment:
                expires_at = existing_payment.expires_at
                if expires_at:
                    expires_at = self.make_aware(expires_at)
                    if expires_at > now_utc:
                        raise HTTPException(status_code=409, detail="Já existe um pagamento pendente e válido para este pedido")

                # Se chegou aqui, o pagamento expirou ou não tem expires_at -> cancela
                existing_payment.status = PaymentStatus.CANCELED
                existing_payment.updated_at = now_utc
                session.add(existing_payment)
                session.commit()

            # Prepara dados do pagador
            full_name = order.customer_name.strip()
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            # Cria pagamento via Mercado Pago
            body = {
                "transaction_amount": data.amount,
                "description": f"Pagamento do pedido #{order.id}, Código: {order.code}",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"pizzariathomaggio@gmail.com", # no-reply@seudominio.com
                    "phone": {
                        "area_code": order.phone[:2],
                        "number": order.phone[2:]
                    },
                    "first_name": first_name,
                    "last_name": last_name,
                },
            }

            result = sdk.payment().create(body)
            response = result["response"]

            if response.get("status") != "pending":
                raise HTTPException(status_code=400, detail="Erro ao gerar QR Code")

            expires_at = now_utc + timedelta(minutes=5)

            # Salva no banco
            payment = Payment(
                order_id=data.order_id,
                method="pix",
                amount=data.amount,
                transaction_code=str(response["id"]),
                status=PaymentStatus.PENDING,
                expires_at=expires_at
            )

            session.add(payment)
            session.commit()
            session.refresh(payment)

            # Extrai QR Code
            poi = response.get('point_of_interaction', {})
            transaction_data = poi.get('transaction_data', {})

            qr_code = transaction_data.get('qr_code')
            qr_code_base64 = transaction_data.get('qr_code_base64')

            if not qr_code or not qr_code_base64:
                raise HTTPException(status_code=400, detail="Dados do QR Code não encontrados na resposta")

            return {
                "qr_code": qr_code,
                "qr_code_base64": qr_code_base64,
                "payment_id": response["id"]
            }

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def handle_webhook(self, request: Request, session: Session = Depends(db_session)):
        try:
            body = await request.json()

            logging.info(f"Webhook recebido: {body}")

            if body.get("type") != "payment":
                return {"status": "ignored"}

            payment_id = body.get("data", {}).get("id")

            if not payment_id:
                return {"status": "no_payment_id"}

            try:
                result = sdk.payment().get(payment_id)
            except Exception as e:
                logging.info(f"Erro ao buscar pagamento {payment_id} - {e}")
                return {"status": "payment_not_found"}

            mp_payment = result.get("response")

            if not mp_payment:
                logging.info(f"Pagamento {payment_id} não encontrado")
                return {"status": "payment_not_found"}

            transaction_code = str(mp_payment["id"])
            status = mp_payment["status"]

            payment = session.exec(
                select(Payment).where(Payment.transaction_code == transaction_code)
            ).first()

            if not payment:
                return {"status": "not_found"}

            if payment.expires_at and payment.expires_at < datetime.now(timezone.utc):
                return {"status": "expired"}

            if status == "approved":
                payment.status = PaymentStatus.PAID
                payment.paid_at = datetime.now(timezone.utc)
            elif status in ["rejected", "cancelled"]:
                payment.status = PaymentStatus.CANCELED
            else:
                payment.status = PaymentStatus.PENDING

            payment.updated_at = datetime.now(timezone.utc)
            session.add(payment)
            session.commit()

            return {"status": "ok"}

        except Exception as e:
            session.rollback()
            logging.error(f"Erro interno no webhook -> {e}")
            return {"status": "internal_error", "detail": str(e)}

    def generate_card_payment(self, data: PaymentRequest, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.id == data.order_id)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")

            # Verifica se já existe pagamento pendente
            existing_payment = session.exec(
                select(Payment).where(
                    Payment.order_id == data.order_id,
                    Payment.status == PaymentStatus.PENDING,
                    Payment.method == "card"
                )
            ).first()

            now_utc = datetime.now(timezone.utc)

            if existing_payment:
                expires_at = existing_payment.expires_at
                if expires_at:
                    expires_at = self.make_aware(expires_at)
                    if expires_at > now_utc:
                        raise HTTPException(status_code=409, detail="Já existe um pagamento pendente e válido para este pedido")
                # Cancela pagamento antigo
                existing_payment.status = PaymentStatus.CANCELED
                existing_payment.updated_at = now_utc
                session.add(existing_payment)
                session.commit()

            # Prepara dados do pagador
            full_name = order.customer_name.strip()
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            # Cria pagamento via Mercado Pago
            body = {
                "transaction_amount": data.amount,
                "token": data.token,  # <<< Importante: token do cartão gerado no frontend
                "description": f"Pagamento do pedido #{order.id}, Código: {order.code}",
                "installments": data.installments or 1,
                "payment_method_id": data.payment_method_id,  # "visa", "master", etc.
                "payer": {
                    "email": f"cartao_cliente_{order.id}@seudominio.com",
                    "first_name": first_name,
                    "last_name": last_name,
                    "identification": {
                        "type": "CPF",
                        "number": data.document_number
                    }
                },
                "capture": True  # Captura automática
            }

            result = sdk.payment().create(body)
            response = result["response"]

            if response.get("status") not in ["approved", "in_process", "pending"]:
                raise HTTPException(status_code=400, detail="Erro ao processar pagamento com cartão")

            expires_at = now_utc + timedelta(minutes=10)  # Cartão: pode ser mais longo

            # Salva no banco
            payment = Payment(
                order_id=data.order_id,
                method="card",
                amount=data.amount,
                transaction_code=str(response["id"]),
                status=PaymentStatus.PENDING if response.get("status") != "approved" else PaymentStatus.PAID,
                expires_at=expires_at
            )

            if payment.status == PaymentStatus.PAID:
                payment.paid_at = now_utc

            session.add(payment)
            session.commit()
            session.refresh(payment)

            return {
                "payment_id": response["id"],
                "status": response["status"],
                "status_detail": response.get("status_detail")
            }

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))


