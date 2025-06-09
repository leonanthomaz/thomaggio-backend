import logging
from fastapi import APIRouter, Depends, Request, Response, Query
from fastapi.responses import JSONResponse
from sqlmodel import Session, select

import httpx

from app.configuration.settings import Configuration
from app.models.order import Order
from app.models.payment import Payment
from app.database.connection import get_session

db_session = get_session
configuration = Configuration()

WHATSAPP_API_URL = configuration.meta_url
WHATSAPP_ACCESS_TOKEN = configuration.facebook_access_token
WHATSAPP_PHONE_ID = configuration.facebook_phone_number_id
VERIFY_TOKEN = configuration.meta_verify_token

class WhatsAppRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/webhook/whatsapp", self.verify_webhook, methods=["GET"])
        self.add_api_route("/webhook/whatsapp", self.whatsapp_webhook, methods=["POST"])
        self.add_api_route("/send-whatsapp", self.send_whatsapp_message, methods=["POST"])

    async def verify_webhook(
        self,
        mode: str = Query(None, alias="hub.mode"),
        challenge: str = Query(None, alias="hub.challenge"),
        verify_token: str = Query(None, alias="hub.verify_token")
    ):
        if mode == "subscribe" and verify_token == VERIFY_TOKEN:
            logging.info("✅ Webhook do WhatsApp verificado com sucesso!")
            return Response(content=challenge, media_type="text/plain")

        logging.error("❌ Falha ao verificar webhook do WhatsApp.")
        return JSONResponse(content={"error": "Token inválido"}, status_code=403)

    async def whatsapp_webhook(self, request: Request):
        try:
            payload = await request.json()
            logging.info(f"📩 Payload recebido do WhatsApp: {payload}")
            return JSONResponse(content={"status": "ok"}, status_code=200)
        except Exception as e:
            logging.error(f"💥 Erro no webhook do WhatsApp: {e}", exc_info=True)
            return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

    async def send_whatsapp_message(self, recipient: str, message: str):
        url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "text",
            "text": {"body": message}
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            logging.info(f"📤 WhatsApp Send: {response.status_code} - {response.text}")
            return response.status_code == 200

    async def send_order_and_payment_info_via_whatsapp(self, order_code: str, session: Session = Depends(db_session)):
        try:
            # Busca o pedido pelo código em vez do ID
            order: Order = session.exec(
                select(Order).where(Order.code == order_code)
            ).first()
            
            if not order:
                logging.warning(f"⚠️ Pedido com código {order_code} não encontrado.")
                return
                
            if not order.whatsapp_id:
                logging.warning(f"⚠️ Pedido {order_code} sem whatsapp_id.")
                return

            payment: Payment = session.exec(
                select(Payment).where(Payment.order_id == order.id)
            ).first()

            message_lines = [
                f"📦 Pedido #{order.code}",
                f"👤 Cliente: {order.customer_name or 'N/A'}",
                f"📞 Telefone: {order.phone or 'N/A'}",
                f"💰 Total: R$ {order.total_amount:.2f}",
                f"💳 Método: {order.payment_method.upper()}",
                f"🔄 Status: {order.payment_status.value.upper()}",
            ]

            if payment:
                if payment.qr_code:
                    message_lines.append(f"🔗 QR Code: {payment.qr_code}")
                if payment.expires_at:
                    message_lines.append(f"⏳ Expira em: {payment.expires_at.strftime('%d/%m/%Y %H:%M')}")
                if payment.paid_at:
                    message_lines.append(f"✅ Pago em: {payment.paid_at.strftime('%d/%m/%Y %H:%M')}")

            message = "\n".join(message_lines)

            success = await self.send_whatsapp_message(order.whatsapp_id, message)
            if not success:
                logging.error(f"❌ Falha ao enviar mensagem para pedido {order_code}")

        except Exception as e:
            logging.error(f"❌ Erro ao enviar info do pedido {order_code} via WhatsApp: {e}", exc_info=True)
        finally:
            session.close()
