# app/websockets/ws_manager.py
from app.websockets.order_ws import OrderWebSocketManager
from app.websockets.payment_ws import PaymentWebSocketManager

order_ws_manager = OrderWebSocketManager()
payment_ws_manager = PaymentWebSocketManager()
