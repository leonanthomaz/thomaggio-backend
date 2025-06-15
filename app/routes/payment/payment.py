from datetime import datetime, timedelta, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.configuration.settings import Configuration
from app.database.connection import get_session
from app.auth.auth import AuthRouter
from app.models.order.order import Order
from app.models.payment.payment import Payment
from app.schemas.payment.payment import PaymentRequest, PaymentResponse
from app.enums.payment_status import PaymentStatus
from app.integration.mercadopago import sdk
from app.tasks.websockets.ws_manager import payment_ws_manager

Configuration()
db_session = get_session
get_current_user = AuthRouter().get_current_user


class PaymentRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/payment/", self.create_payment, methods=["POST"], response_model=dict)
        self.add_api_route("/payment/pix-qrcode", self.generate_pix_qrcode, methods=["POST"], response_model=dict)
        self.add_api_route("/payment/retry/pix-qrcode", self.regenerate_pix_qrcode, methods=["POST"], response_model=dict)
        self.add_api_route("/payment/webhook", self.handle_webhook, methods=["POST"])
        self.add_api_route("/payment/{order_code}", self.get_payment, methods=["GET"], response_model=PaymentResponse)
        self.add_api_route("/payment/{order_code}/status", self.check_pix_status, methods=["GET"], response_model=dict)
        self.add_api_route("/payment/{order_code}/change-method", self.change_payment_method, methods=["PATCH"], response_model=dict)
        self.add_api_route("/payment/transaction/{transaction_code}", self.get_payment_by_transaction_code, methods=["GET"], response_model=PaymentResponse)

    def check_pix_status(self, order_code: str, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.code == order_code)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")

            payment = session.exec(
                select(Payment)
                .where(Payment.order_id == order.id, Payment.method == "pix")
                .order_by(Payment.created_at.desc())
            ).first()

            if not payment:
                return {"status": "not_found"}

            now_utc = datetime.now(timezone.utc)
            expired = payment.expires_at and payment.expires_at < now_utc

            return {
                "status": payment.status.value,
                "expired": expired,
                "expires_at": payment.expires_at.isoformat() if payment.expires_at else None,
                "created_at": payment.created_at.isoformat() if payment.created_at else None
            }

        except Exception as e:
            logging.error(f"Erro ao verificar status do pagamento: {str(e)}")
            raise HTTPException(status_code=500, detail="Erro ao verificar status do pagamento")

    def create_payment(self, data: PaymentRequest, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.id == data.order_id)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")
            
            if data.method == "pix":
                return self.generate_pix_qrcode(data, session)

            # Pagamento comum
            expiration_time = datetime.now(timezone.utc) + timedelta(minutes=1)
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

            return {
                "payment_id": payment.id,
                "status": payment.status.value,
                "expires_at": payment.expires_at.isoformat()
            }

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    def get_payment(self, order_code: str, session: Session = Depends(db_session)):
            try:
                order = session.exec(select(Order).where(Order.code == order_code)).first()

                if not order:
                    raise HTTPException(status_code=404, detail="Pedido não encontrado")

                payment = session.exec(
                    select(Payment)
                    .where(Payment.order_id == order.id)
                ).first()

                if not payment:
                    raise HTTPException(status_code=404, detail="Pagamento não encontrado")

                return PaymentResponse(
                    id=payment.id,
                    order_id=payment.order_id,
                    method=payment.method,
                    amount=payment.amount,
                    status=payment.status,
                    transaction_code=payment.transaction_code,
                    expires_at=payment.expires_at.isoformat() if payment.expires_at else None,
                    paid_at=payment.paid_at.isoformat() if payment.paid_at else None,
                    created_at=payment.created_at.isoformat(),
                    updated_at=payment.updated_at.isoformat() if payment.updated_at else None,
                    qr_code=payment.qr_code,
                    qr_code_base64=payment.qr_code_base64
                )
                
            except Exception as e:
                logging.error(f"PAGAMENTO >>> Erro ao buscar pagamento: {str(e)}")
                raise HTTPException(status_code=500, detail="Erro interno ao buscar pagamento")

    def generate_pix_qrcode(self, data: PaymentRequest, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.id == data.order_id)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")
            
            logging.info(f"PAGAMENTO >>> PEDIDO ENVIADO: {order}")

            now_utc = datetime.now(timezone.utc)

            # Busca pagamento anterior (caso exista)
            existing_payment = session.exec(
                select(Payment)
                .where(Payment.order_id == order.id, Payment.method == "pix")
                .order_by(Payment.created_at.desc())
            ).first()
            
            logging.info(f"PAGAMENTO >>> PEDIDO EXISTENTE: {existing_payment}")

            if existing_payment:
                if existing_payment.expires_at and existing_payment.expires_at > now_utc:
                    # Ainda tá válido
                    return {
                        "qr_code": existing_payment.qr_code,
                        "qr_code_base64": existing_payment.qr_code_base64,
                        "transaction_code": existing_payment.transaction_code,
                        "expires_at": existing_payment.expires_at.isoformat(),
                        "status": "pending"
                    }
                else:
                    # Expirado, marca como cancelado
                    existing_payment.status = PaymentStatus.CANCELED
                    session.add(existing_payment)
                    session.commit()

            # Gera novo PIX via MP
            full_name = order.customer_name.strip()
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            body = {
                "transaction_amount": data.amount,
                "description": f"Pedido #{order.code}",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"cliente_{order.id}@temp.com",
                    "first_name": first_name,
                    "last_name": last_name,
                },
            }
            
            logging.info(f"PAGAMENTO >>> BODY PARA O PIX: {body}")

            result = sdk.payment().create(body)
            logging.info(f"PAGAMENTO >>> RESULTADO DO SDK: {result}")

            response = result.get("response")
            if not response:
                raise HTTPException(status_code=500, detail="Erro ao se comunicar com o Mercado Pago")

            if response.get("status") != "pending":
                raise HTTPException(status_code=400, detail="Erro ao gerar PIX")
            
            logging.info(f"RESPOSTA DO PAGAMENTO >>> {response}")

            poi = response.get("point_of_interaction", {})
            transaction_data = poi.get("transaction_data", {})
            qr_code = transaction_data.get("qr_code")
            qr_code_base64 = transaction_data.get("qr_code_base64")
            transaction_code = str(response["id"])

            if not qr_code:
                raise HTTPException(status_code=400, detail="QR Code não gerado")
            
            expires_at = now_utc + timedelta(minutes=10)
            payment = Payment(
                order_id=order.id,
                method="pix",
                amount=data.amount,
                transaction_code=transaction_code,
                status=PaymentStatus.PENDING,
                expires_at=expires_at,
                qr_code=qr_code,
                qr_code_base64=qr_code_base64,
                created_at=now_utc
            )
            logging.info(f"PAGAMENTO >>> A SER SALVO: {payment}")
            session.add(payment)
            session.commit()
            session.refresh(payment)

            return {
                "qr_code": qr_code,
                "qr_code_base64": qr_code_base64,
                "transaction_code": transaction_code,
                "expires_at": payment.expires_at.isoformat()
            }

        except Exception as e:
            session.rollback()
            logging.error(f"Erro ao gerar PIX: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao processar PIX: {str(e)}")

    async def handle_webhook(self, request: Request, session: Session = Depends(db_session)):
        try:
            body = await request.json()

            logging.info(f"MERCADO PAGO >>> Webhook recebido: {body}")

            if body.get("type") != "payment":
                return {"status": "ignored"}

            payment_id = body.get("data", {}).get("id")

            if not payment_id:
                return {"status": "no_payment_id"}

            try:
                result = sdk.payment().get(payment_id)
            except Exception as e:
                logging.error(f"MERCADO PAGO >>> Erro ao buscar pagamento {payment_id} - {e}")
                return {"status": "payment_not_found"}

            mp_payment = result.get("response")

            if not mp_payment:
                logging.error(f"MERCADO PAGO >>> Pagamento {payment_id} não encontrado")
                return {"status": "payment_not_found"}

            transaction_code = str(mp_payment["id"])
            status = mp_payment["status"]

            payment = session.exec(
                select(Payment).where(Payment.transaction_code == transaction_code)
            ).first()

            if not payment:
                return {"status": "not_found"}

            expires_at = payment.expires_at
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)

            if expires_at and expires_at < datetime.now(timezone.utc):
                return {"status": "expired"}

            if status == "approved":
                payment.status = PaymentStatus.PAID
                payment.paid_at = datetime.now(timezone.utc)
                payment.qr_code_base64 = None
            elif status in ["rejected", "cancelled"]:
                payment.status = PaymentStatus.CANCELED
                payment.qr_code_base64 = None
            elif payment.expires_at and payment.expires_at < datetime.now(timezone.utc):
                payment.status = PaymentStatus.CANCELED
                payment.qr_code_base64 = None
            else:
                payment.status = PaymentStatus.PENDING
                

            payment.updated_at = datetime.now(timezone.utc)
            session.add(payment)
            session.commit()
            
            await payment_ws_manager.broadcast({
                "type": "payment_status",
                "transaction_code": transaction_code,
                "status": payment.status.value,
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None
            })

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

    def get_payment_by_transaction_code(self, transaction_code: str, session: Session = Depends(db_session)):
        try:
            payment = session.exec(select(Payment).where(Payment.transaction_code == transaction_code)).first()
            if not payment:
                raise HTTPException(status_code=404, detail="Pagamento não encontrado")
            return payment
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        
    def regenerate_pix_qrcode(self, data: PaymentRequest, session: Session = Depends(db_session)):
        try:
            order = session.exec(select(Order).where(Order.id == data.order_id)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")

            now_utc = datetime.now(timezone.utc)

            # Busca o último pagamento Pix
            existing_payment = session.exec(
                select(Payment)
                .where(Payment.order_id == order.id, Payment.method == "pix")
                .order_by(Payment.created_at.desc())
            ).first()

            if existing_payment:
                if existing_payment.status == PaymentStatus.PAID:
                    raise HTTPException(status_code=400, detail="Pagamento já foi realizado")
                if existing_payment.status == PaymentStatus.PENDING:
                    raise HTTPException(status_code=400, detail="Existe um pagamento ativo.")
                else:
                    # Expirado, marca como cancelado
                    existing_payment.status = PaymentStatus.CANCELED
                    existing_payment.qr_code_base64 = None
                    existing_payment.updated_at = now_utc
                    session.add(existing_payment)
                    session.commit()

            # Gera novo PIX via MP
            full_name = order.customer_name.strip()
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

            body = {
                "transaction_amount": data.amount,
                "description": f"Pedido #{order.code}",
                "payment_method_id": "pix",
                "payer": {
                    "email": f"cliente_{order.id}@temp.com",
                    "first_name": first_name,
                    "last_name": last_name,
                },
            }

            result = sdk.payment().create(body)
            response = result["response"]

            if response.get("status") != "pending":
                raise HTTPException(status_code=400, detail="Erro ao gerar PIX")

            poi = response.get("point_of_interaction", {})
            transaction_data = poi.get("transaction_data", {})
            qr_code = transaction_data.get("qr_code")
            qr_code_base64 = transaction_data.get("qr_code_base64")
            transaction_code = str(response["id"])

            if not qr_code:
                raise HTTPException(status_code=400, detail="QR Code não gerado")

            expires_at = now_utc + timedelta(minutes=10)
            payment = Payment(
                order_id=order.id,
                method="pix",
                amount=data.amount,
                transaction_code=transaction_code,
                status=PaymentStatus.PENDING,
                expires_at=expires_at,
                qr_code=qr_code,
                qr_code_base64=qr_code_base64,
                created_at=now_utc
            )
            session.add(payment)
            session.commit()
            session.refresh(payment)

            return {
                "qr_code": qr_code,
                "qr_code_base64": qr_code_base64,
                "transaction_code": transaction_code,
                "expires_at": payment.expires_at.isoformat()
            }

        except Exception as e:
            session.rollback()
            logging.error(f"Erro ao gerar PIX: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro ao processar PIX: {str(e)}")

        except Exception as e:
            session.rollback()
            logging.error(f"Erro ao regenerar QR Code do Pix: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Erro ao tentar regenerar o Pix")

    def make_aware(self, dt: datetime) -> datetime:
        """Convert naive datetime to timezone-aware (UTC)"""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
    def now_utc(self) -> datetime:
        """Get current time with UTC timezone"""
        return datetime.now(timezone.utc)
    
    
    def change_payment_method(
        self, 
        order_code: str, 
        data: dict,
        session: Session = Depends(db_session)
    ):
        """
        Altera o método de pagamento de um pedido existente.
        
        Para 'dinheiro' requer o campo 'cash_change_for' (valor dado pelo cliente).
        Para 'cartao' apenas altera o método (implementação futura).
        Para 'pix' apenas altera o método (já implementado).
        """
        try:
            # Busca o pedido
            order = session.exec(select(Order).where(Order.code == order_code)).first()
            if not order:
                raise HTTPException(status_code=404, detail="Pedido não encontrado")
            
            new_method = data.get("method")
            if not new_method or new_method not in ["pix", "dinheiro", "cartao"]:
                raise HTTPException(status_code=400, detail="Método de pagamento inválido")
            
            # Verifica se há mudança real
            if order.payment_method == new_method:
                return {"status": "success", "message": "Método de pagamento já é o mesmo"}
            
            # Reseta campos de dinheiro se não for o método selecionado
            if new_method != "dinheiro":
                order.cash_change_for = None
                order.cash_change = None
            
            # Lógica específica para cada método
            if new_method == "dinheiro":
                cash_change_for = data.get("cash_change_for")
                if cash_change_for is None or cash_change_for <= 0:
                    raise HTTPException(
                        status_code=400, 
                        detail="Para pagamento em dinheiro, informe o valor recebido para cálculo de troco"
                    )
                
                # Calcula o troco
                if cash_change_for < order.total_amount:
                    raise HTTPException(
                        status_code=400,
                        detail="O valor recebido deve ser maior ou igual ao total do pedido"
                    )
                
                order.cash_change_for = cash_change_for
                order.cash_change = cash_change_for - order.total_amount
            
            # Atualiza o método de pagamento no pedido
            order.payment_method = new_method
            order.updated_at = datetime.now(timezone.utc)
            session.add(order)
            
            now_utc = datetime.now(timezone.utc)
            
            # Busca pagamentos existentes para este pedido
            existing_payments = session.exec(
                select(Payment)
                .where(Payment.order_id == order.id)
            ).all()
            
            # Se mudou para PIX, cancela todos os pagamentos existentes e cria um novo PIX
            if new_method == "pix":
                # Cancela todos os pagamentos existentes
                for payment in existing_payments:
                    payment.status = PaymentStatus.CANCELED
                    payment.updated_at = datetime.now(timezone.utc)
                    session.add(payment)
                
                # Gera novo PIX
                full_name = order.customer_name.strip()
                parts = full_name.split(" ", 1)
                first_name = parts[0]
                last_name = parts[1] if len(parts) > 1 else ""

                body = {
                    "transaction_amount": order.total_amount,
                    "description": f"Pedido #{order.code}",
                    "payment_method_id": "pix",
                    "payer": {
                        "email": f"cliente_{order.id}@temp.com",
                        "first_name": first_name,
                        "last_name": last_name,
                    },
                }

                result = sdk.payment().create(body)
                response = result["response"]

                if response.get("status") != "pending":
                    raise HTTPException(status_code=400, detail="Erro ao gerar PIX")

                poi = response.get("point_of_interaction", {})
                transaction_data = poi.get("transaction_data", {})
                qr_code = transaction_data.get("qr_code")
                qr_code_base64 = transaction_data.get("qr_code_base64")
                transaction_code = str(response["id"])

                if not qr_code:
                    raise HTTPException(status_code=400, detail="QR Code não gerado")

                
                expires_at = now_utc + timedelta(minutes=10)
                # Cria novo registro de pagamento PIX
                new_payment = Payment(
                    order_id=order.id,
                    method="pix",
                    amount=order.total_amount,
                    transaction_code=transaction_code,
                    status=PaymentStatus.PENDING,
                    expires_at=expires_at,
                    qr_code=qr_code,
                    qr_code_base64=qr_code_base64,
                    created_at=now_utc
                )
                session.add(new_payment)
                session.commit()
                session.refresh(new_payment)
                
                return {
                    "qr_code": qr_code,
                    "qr_code_base64": qr_code_base64,
                    "transaction_code": transaction_code,
                    "expires_at": expires_at.isoformat(),
                }
            else:
                # Para dinheiro ou cartão, cancela todos os pagamentos PIX existentes
                # e limpa os dados de QR code
                for payment in existing_payments:
                    if payment.method == "pix" and payment.status == PaymentStatus.PENDING:
                        payment.status = PaymentStatus.CANCELED
                        payment.qr_code = None
                        payment.qr_code_base64 = None
                        payment.updated_at = datetime.now(timezone.utc)
                        session.add(payment)

                # Cria novo pagamento com o método atualizado
                new_payment = Payment(
                    order_id=order.id,
                    method=new_method,
                    amount=order.total_amount,
                    status=PaymentStatus.PENDING,
                    created_at=datetime.now(timezone.utc)
                )
                session.add(new_payment)

                session.commit()
                
                return {
                    "status": "success",
                    "order_code": order.code,
                    "new_method": new_method,
                    "cash_change": order.cash_change if new_method == "dinheiro" else None
                }
                
        except HTTPException:
            raise  # Re-lança exceções HTTP que já foram tratadas
        except Exception as e:
            session.rollback()
            logging.error(f"Erro ao alterar método de pagamento: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail="Erro interno ao alterar método de pagamento"
            )
