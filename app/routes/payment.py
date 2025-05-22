from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.database.connection import get_session
from app.auth.auth import AuthRouter
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import PaymentRequest, PaymentResponse
from app.enums.payment_status import PaymentStatus
from app.api.mercadopago import sdk

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

            payment = Payment(
                order_id=data.order_id,
                method=data.method,
                amount=data.amount,
                status=PaymentStatus.PENDING,
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

            if existing_payment:
                raise HTTPException(status_code=409, detail="Já existe um pagamento pendente para este pedido")

            # Cria pagamento via Mercado Pago
            body = {
                "transaction_amount": data.amount,
                "description": f"Pagamento do pedido #{order.id}",
                "payment_method_id": "pix",
                "payer": {
                    "email": "cliente@email.com",
                    "first_name": "Cliente",
                    "last_name": "Teste",
                },
            }

            result = sdk.payment().create(body)
            response = result["response"]

            if response["status"] != "pending":
                raise HTTPException(status_code=400, detail="Erro ao gerar QR Code")

            # Salva no banco
            payment = Payment(
                order_id=data.order_id,
                method="pix",
                amount=data.amount,
                transaction_code=str(response["id"]),
                status=PaymentStatus.PENDING
            )

            session.add(payment)
            session.commit()
            session.refresh(payment)

            return {
                "qr_code": response["point_of_interaction"]["transaction_data"]["qr_code"],
                "qr_code_base64": response["point_of_interaction"]["transaction_data"]["qr_code_base64"],
                "payment_id": response["id"]
            }

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def handle_webhook(self, request: Request, session: Session = Depends(db_session)):
        try:
            body = await request.json()

            if body.get("type") != "payment":
                return {"status": "ignored"}

            payment_id = body.get("data", {}).get("id")
            result = sdk.payment().get(payment_id)
            mp_payment = result["response"]

            transaction_code = str(mp_payment["id"])
            status = mp_payment["status"]

            payment = session.exec(
                select(Payment).where(Payment.transaction_code == transaction_code)
            ).first()

            if not payment:
                return {"status": "not_found"}

            if status == "approved":
                payment.status = PaymentStatus.PAID
                payment.paid_at = datetime.now(timezone.utc)
            elif status in ["rejected", "cancelled"]:
                payment.status = PaymentStatus.CANCELLED
            else:
                payment.status = PaymentStatus.PENDING

            payment.updated_at = datetime.now(timezone.utc)
            session.add(payment)
            session.commit()

            return {"status": "ok"}

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
