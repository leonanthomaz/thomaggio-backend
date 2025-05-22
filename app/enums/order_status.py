from enum import Enum

# pending, preparing, ready, delivered, canceled
class OrderStatus(str, Enum):
    PENDING = "pending"         
    PREPARING = "preparing" 
    READY = "ready"   
    DELIVERED = "delivered"   
    CANCELED = "canceled"       
