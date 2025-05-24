# app/cache/cache.py
import logging
from typing import Optional
from app.models.category import Category
from app.models.delivery_config import DeliveryConfig
from app.schemas.product import ProductResponse
from app.utils.cache import DataCache
from sqlmodel import Session, select
from app.models.company import Company
from app.models.product import Product

cache = DataCache()

class CacheManager:
    _cache_key_prefix = "main_data_"
    
    def __init__(self):
        self.cache = cache

    def get_cache_key(self, key: str) -> str:
        """Gera a chave de cache completa com o prefixo"""
        return f"{self._cache_key_prefix}{key}"

    async def load_cached_data(self, key: str) -> Optional[dict]:
        """Carrega dados do cache"""
        cache_key = self.get_cache_key(key)
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logging.info(f"Dados encontrados no cache para a chave: {cache_key}")
        return cached_data

    async def cache_data(self, key: str, data: dict) -> None:
        """Armazena dados no cache"""
        cache_key = self.get_cache_key(key)
        self.cache.set(cache_key, data, ttl=900)
        logging.info(f"Dados armazenados no cache com a chave: {cache_key}")

 
    async def get_company_data(self, session: Session) -> dict:
        """Obtém dados da empresa, usando cache quando possível"""
        cache_key = "company_data"
        cached = await self.load_cached_data(cache_key)

        if cached:
            chatbot_status = session.exec(select(Company.chatbot_status)).first()
            status = session.exec(select(Company.status)).first()
            cached["chatbot_status"] = chatbot_status.value if chatbot_status else "INACTIVE"
            cached["status"] = status.value if status else "OPEN"
            return cached

        company = session.exec(select(Company)).first()
        company_data = {
            "nome": company.name if company else "Empresa",
            "chatbot_status": company.chatbot_status.value if company and company.chatbot_status else "INACTIVE",
            "status": company.status.value if company and company.chatbot_status else "OPEN",
            "endereco": (company.addresses[0].street if company and company.addresses else "Endereço não disponível"),
            "horario_funcionamento": (
                f"{company.opening_time.strftime('%H:%M')} às {company.closing_time.strftime('%H:%M')}"
                if company and company.opening_time and company.closing_time else "Horário não disponível"
            ),
            "dias_funcionamento": company.working_days if company and company.working_days else [],
            "redes_sociais": company.social_media_links if company and company.social_media_links else {},
        }

        await self.cache_data(cache_key, company_data)
        return company_data

 
    async def get_products_data(self, session: Session) -> dict:
        """Obtém dados de produtos e categorias, usando cache quando possível"""
        cache_key = "product_data"
        cached = await self.load_cached_data(cache_key)
        if cached:
            return cached

        products = session.exec(select(Product)).all()
        produtos_disponiveis = [
            ProductResponse.model_validate(product).model_dump()
            for product in products
        ]

        categories = [
            c.name for c in session.exec(select(Category).where(Category.is_active)).all()
        ]

        data = {
            "products": produtos_disponiveis,
            "categories": categories
        }

        await self.cache_data(cache_key, data)
        return data


    
    async def get_delivery_config_data(self, session: Session) -> dict:
        """Obtém dados de entrega, usando cache quando possível"""
        cache_key = "delivery_data"
        cached = await self.load_cached_data(cache_key)
        if cached:
            return cached

        config = session.exec(select(DeliveryConfig)).first()
        
        await self.cache_data(cache_key, config.dict() if config else {})

        return config.dict() if config else {}
