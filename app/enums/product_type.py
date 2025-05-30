from enum import Enum

class ProductTypeEnum(str, Enum):
    pizza = "pizza"
    bebida = "bebida"
    salgado = "salgado"
    combo = "combo"
    geral = "geral"
