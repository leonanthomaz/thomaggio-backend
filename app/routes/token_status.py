import os
from app.configuration.settings import Configuration
import httpx
import logging
from fastapi import APIRouter, HTTPException, status
from enum import Enum

# Configuração de logging
logging.basicConfig(level=logging.INFO)

configuration = Configuration()

class Provider(str, Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"

class TokenStatusRouter(APIRouter):
    """
    Roteador para verificar o status dos tokens de provedores de IA.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
        self.add_api_route("/check_token_status/{provider}", self.check_token_status, methods=["GET"])

    async def check_openai_status(self, api_key: str) -> dict:
        """
        Verifica o status do token para o OpenAI.

        Args:
            api_key (str): Chave de API do OpenAI.

        Returns:
            dict: Informações sobre o status do token.

        Raises:
            HTTPException: Se ocorrer um erro ao acessar o OpenAI.
        """
        url = "https://openrouter.ai/api/v1/auth/key"
        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            logging.info("Fazendo requisição para o OpenAI")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            data = response.json()
            key_info = data.get("data", {})
            logging.info(f"Status da resposta do OpenAI: {response.status_code}")
            logging.info(f"Créditos usados: {key_info.get('usage')}, Limite de créditos: {key_info.get('limit')}")
            logging.info(f"Rate Limit Requests: {key_info['rate_limit']['requests']}, Intervalo: {key_info['rate_limit']['interval']}")
            return {
                "provider": "OpenAI",
                "label": key_info.get("label"),
                "credits_used": key_info.get("usage"),
                "credit_limit": key_info.get("limit"),
                "is_free_tier": key_info.get("is_free_tier"),
                "rate_limit_requests": key_info["rate_limit"]["requests"],
                "rate_limit_interval": key_info["rate_limit"]["interval"],
            }
        except httpx.HTTPStatusError as e:
            logging.error(f"Erro ao acessar OpenAI: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro ao acessar OpenAI: {e}")
        except httpx.RequestError as e:
            logging.error(f"Erro ao acessar OpenAI: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao acessar OpenAI: {e}")

    async def check_deepseek_status(self, api_key: str) -> dict:
        """
        Verifica o status do token para o DeepSeek.

        Args:
            api_key (str): Chave de API do DeepSeek.

        Returns:
            dict: Informações sobre o status do token.

        Raises:
            HTTPException: Se ocorrer um erro ao acessar o DeepSeek.
        """
        url = "https://api.deepseek.com/v1/status"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            logging.info("Fazendo requisição para o DeepSeek")
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
            data = response.json()
            logging.info(f"Status da resposta do DeepSeek: {response.status_code}")
            logging.info(f"Créditos usados: {data.get('usage', {}).get('used', 0)}, Limite de créditos: {data.get('usage', {}).get('limit', 0)}")
            logging.info(f"Rate Limit Requests: {data.get('rate_limit', {}).get('requests', 0)}, Intervalo: {data.get('rate_limit', {}).get('interval', 'N/A')}")
            
            return {
                "provider": "DeepSeek",
                "credits_used": data.get("usage", {}).get("used", 0),
                "credit_limit": data.get("usage", {}).get("limit", 0),
                "rate_limit_requests": data.get("rate_limit", {}).get("requests", 0),
                "rate_limit_interval": data.get("rate_limit", {}).get("interval", "N/A"),
            }
        except httpx.HTTPStatusError as e:
            logging.error(f"Erro ao acessar DeepSeek: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro ao acessar DeepSeek: {e}")
        except httpx.RequestError as e:
            logging.error(f"Erro ao acessar DeepSeek: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao acessar DeepSeek: {e}")

    async def check_token_status(self, provider: Provider):
        """
        Verifica o status do token para o provedor especificado.

        Args:
            provider (Provider): Provedor de IA (openai ou deepseek).

        Returns:
            dict: Informações sobre o status do token.

        Raises:
            HTTPException: Se o provedor for inválido ou a chave não estiver configurada.
        """
        logging.info(f"Verificando status do token para o provedor: {provider.value}")
        if provider == Provider.OPENAI and self.openai_api_key:
            return await self.check_openai_status(self.openai_api_key)
        elif provider == Provider.DEEPSEEK and self.deepseek_api_key:
            return await self.check_deepseek_status(self.deepseek_api_key)
        else:
            logging.error("Provedor inválido ou chave não configurada corretamente.")
            raise HTTPException(status_code=status.HTTP_BAD_REQUEST, detail="Provedor inválido ou chave não configurada corretamente.")
