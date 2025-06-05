# app/websockets/routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets.ws_manager import order_ws_manager, payment_ws_manager

router = APIRouter()

@router.websocket("/ws/orders")
async def websocket_orders(websocket: WebSocket):
    await order_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        order_ws_manager.disconnect(websocket)
        
@router.websocket("/ws/payment/{transaction_code}")
async def websocket_payment(websocket: WebSocket):
    await payment_ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        payment_ws_manager.disconnect(websocket)
