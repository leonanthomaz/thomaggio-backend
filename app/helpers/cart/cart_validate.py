# app/services/cart_validators.py

from app.models.cart.cart import Cart

def validate_minimum_order_value(cart: Cart, min_value: float = 20.0):
    if cart.total < min_value:
        raise ValueError(f"Pedido mínimo é de R$ {min_value:.2f}. Seu total: R$ {cart.total:.2f}")

def validate_not_only_beverages(cart: Cart):
    if all(item.product.category == "bebidas" for item in cart.items):
        raise ValueError("Não é permitido pedir apenas bebidas.")

def validate_minimum_items(cart: Cart, min_qty: int = 2):
    if cart.total_items < min_qty:
        raise ValueError(f"O pedido deve ter pelo menos {min_qty} itens.")
