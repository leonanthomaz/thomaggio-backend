# app/websockets/ws_manager.py
from app.tasks.websockets.order_ws import OrderWebSocketManager
from app.tasks.websockets.payment_ws import PaymentWebSocketManager

order_ws_manager = OrderWebSocketManager()
payment_ws_manager = PaymentWebSocketManager()
