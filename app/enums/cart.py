from enum import Enum

class CartStatus(str, Enum):
    ACTIVE = "active"         # Carrinho em edição
    PROCESSING = "processing" # Pedido enviado, em preparo
    COMPLETED = "completed"   # Pedido entregue
    CANCELLED = "cancelled"   # Cancelado manualmente
    EXPIRED = "expired"       # Abandonado/inativo por tempo demais
