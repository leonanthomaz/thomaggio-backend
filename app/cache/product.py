# import logging
# from typing import Optional, List, Dict, Any
# from datetime import datetime, timedelta
# from sqlmodel import Session, select
# from app.models.product import Product
# from app.models.category import Category
# from app.utils.cache import DataCache

# logger = logging.getLogger(__name__)

# class ProductCacheManager:
#     _cache_key_prefix = "pdv_products_"
#     _default_ttl = 900  # 15 minutos em segundos
    
#     def __init__(self):
#         self.cache = DataCache()
    
#     def get_cache_key(self, suffix: str = "") -> str:
#         """Gera a chave de cache completa"""
#         return f"{self._cache_key_prefix}{suffix}" if suffix else self._cache_key_prefix
    
#     def get_products_cache(self) -> Optional[List[Dict[str, Any]]]:
#         """Obtém produtos do cache"""
#         cache_key = self.get_cache_key("all_active")
#         return self.cache.get(cache_key)
    
#     def set_products_cache(self, products: List[Dict[str, Any]]) -> None:
#         """Armazena produtos no cache"""
#         cache_key = self.get_cache_key("all_active")
#         self.cache.set(cache_key, products, ttl=self._default_ttl)
#         logger.info(f"Cache de produtos atualizado - {len(products)} itens")
    
#     def clear_products_cache(self) -> None:
#         """Limpa o cache de produtos"""
#         cache_key = self.get_cache_key("all_active")
#         self.cache.clear(cache_key)
#         logger.info("Cache de produtos limpo")
    
#     async def get_all_active_products(self, session: Session) -> List[Dict[str, Any]]:
#         """
#         Obtém todos os produtos ativos, usando cache quando possível.
#         Retorna uma lista de dicionários com os dados dos produtos.
#         """
#         cached_products = self.get_products_cache()
#         if cached_products is not None:
#             logger.debug("Retornando produtos do cache")
#             return cached_products
        
#         # Busca do banco se não estiver em cache
#         logger.debug("Buscando produtos do banco de dados")
#         products = session.exec(
#             select(Product).where(Product.is_active == True)
#         ).all()
        
#         # Converte para dicionário (serializável)
#         products_data = [product.dict() for product in products]
        
#         # Armazena no cache
#         self.set_products_cache(products_data)
        
#         return products_data
