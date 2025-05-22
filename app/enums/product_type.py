from enum import Enum

class ProductTypeEnum(str, Enum):
    pizza = "pizza"
    bebida = "bebida"
    salgado = "salgado"
    geral = "geral"
