from sqlalchemy import Enum


class ProductFlavorEnum(str, Enum):
    frango = "Frango"
    carne = "Carne"
    queijo = "Queijo"
