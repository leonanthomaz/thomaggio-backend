from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import ValidationError

from app.auth.auth import AuthRouter
from app.core.middlewares.users import is_admin
from app.models.company.company import Company
from app.models.user.user import User
from app.schemas.company.address import AddressUpdate
from app.schemas.chat.chat_status import ChatbotStatusUpdate, StatusResponse
from app.schemas.company.company import CompanyStatusResponse, CompanyStatusUpdate, CompanyUpdate
from app.database.connection import get_session
from app.core.exceptions.app_exception import AppHttpException

db_session = get_session
get_current_user = AuthRouter().get_current_user

class CompanyRouter(APIRouter):
    """
    Roteador para operações relacionadas a empresas com tratamento robusto de erros.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = "/company"
        self.tags = ["company"]
        
        self.add_api_route("", self.get_company, methods=["GET"], 
                         response_model=Company,
                         summary="Obter dados da empresa",
                         responses={
                             404: {"description": "Empresa não encontrada"},
                             500: {"description": "Erro interno no servidor"}
                         })
        
        self.add_api_route("/status", self.company_read_status, methods=["GET"], 
                         response_model=CompanyStatusResponse,
                         summary="Obter status da empresa",
                         responses={
                             404: {"description": "Empresa não encontrada"},
                             500: {"description": "Erro interno no servidor"}
                         })
        
        self.add_api_route("/status", self.change_company_status, methods=["POST"], 
                         response_model=CompanyStatusResponse,
                         summary="Alterar status da empresa",
                         responses={
                             400: {"description": "Dados inválidos"},
                             404: {"description": "Empresa não encontrada"},
                             500: {"description": "Erro interno no servidor"}
                         })
        
        self.add_api_route("/chatbot-status", self.chatbot_read_status, methods=["GET"], 
                         response_model=StatusResponse,
                         summary="Obter status do chatbot",
                         responses={
                             404: {"description": "Empresa não encontrada"},
                             500: {"description": "Erro interno no servidor"}
                         })
        
        self.add_api_route("/chatbot-status", self.chatbot_change_status, methods=["POST"], 
                         response_model=StatusResponse,
                         summary="Alterar status do chatbot",
                         responses={
                             400: {"description": "Dados inválidos"},
                             404: {"description": "Empresa não encontrada"},
                             500: {"description": "Erro interno no servidor"}
                         })
        
        self.add_api_route("/health", self.check_health, methods=["GET"],
                         summary="Verificar saúde do serviço")
        
        self.add_api_route("/{company_id}", self.update_company, methods=["PUT"], 
                         response_model=Company,
                         summary="Atualizar dados da empresa",
                         responses={
                             400: {"description": "Dados inválidos"},
                             403: {"description": "Acesso não autorizado"},
                             404: {"description": "Empresa não encontrada"},
                             500: {"description": "Erro interno no servidor"}
                         })
            
    def check_health(self) -> dict:
        """Endpoint de verificação de saúde do serviço"""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
            
    async def get_company(self, session: Session = Depends(db_session)) -> Company:
        """
        Retorna os dados da empresa principal.
        
        Raises:
            HTTPException: 404 se empresa não encontrada
            HTTPException: 500 para erros inesperados
        """
        try:
            company = session.exec(select(Company).where(Company.id == 1)).first()
            if not company:
                raise AppHttpException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Empresa não encontrada.",
                    solution="Verifique se a empresa foi corretamente cadastrada."
                )
            return company
            
        except Exception as e:
            logger.error(f"Erro ao buscar empresa: {str(e)}", exc_info=True)
            raise AppHttpException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao buscar dados da empresa",
                solution="Tente novamente mais tarde ou contate o suporte."
            )

    async def update_company(
        self, 
        company_id: int,
        company: CompanyUpdate, 
        current_user: User = Depends(get_current_user), 
        session: Session = Depends(db_session)
    ) -> Company:
        """
        Atualiza os dados da empresa com tratamento completo de erros.
        
        Args:
            company_id: ID da empresa a ser atualizada
            company: Dados atualizados da empresa
            current_user: Usuário autenticado
            session: Sessão do banco de dados
            
        Returns:
            Company: Empresa atualizada
            
        Raises:
            HTTPException: Para vários cenários de erro
        """
        try:
            # Verificação de autorização
            is_admin(current_user)
            
            # Validação adicional dos dados
            try:
                company.model_validate(company.model_dump())
            except ValidationError as ve:
                raise AppHttpException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Dados inválidos fornecidos",
                    errors=ve.errors(),
                    solution="Verifique os dados e tente novamente."
                )

            # Busca empresa
            db_company = session.exec(select(Company).where(Company.id == company_id)).first()
            if not db_company:
                raise AppHttpException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Empresa com ID {company_id} não encontrada",
                    solution="Verifique o ID da empresa."
                )

            # Atualização transacional
            try:
                # Atualiza campos simples
                update_data = company.model_dump(exclude_unset=True, exclude={"addresses"})
                for key, value in update_data.items():
                    setattr(db_company, key, value)

                # Atualiza endereços
                if company.addresses is not None:
                    self._update_company_addresses(db_company, company.addresses, session)

                db_company.updated_at = datetime.now(timezone.utc)
                session.add(db_company)
                session.commit()
                session.refresh(db_company)
                
                return db_company
                
            except Exception as e:
                session.rollback()
                logger.error(f"Erro durante atualização da empresa: {str(e)}", exc_info=True)
                raise AppHttpException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Falha durante a atualização dos dados",
                    solution="Tente novamente ou contate o suporte."
                )
                
        except HTTPException:
            raise  # Re-lança exceções HTTP já tratadas
        except Exception as e:
            logger.error(f"Erro inesperado ao atualizar empresa: {str(e)}", exc_info=True)
            raise AppHttpException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao atualizar empresa",
                solution="Tente novamente mais tarde."
            )

    def _update_company_addresses(
        self, 
        db_company: Company, 
        addresses: list[AddressUpdate], 
        session: Session
    ) -> None:
        """Método auxiliar para atualização de endereços com tratamento de erros"""
        try:
            old_addresses = {addr.id: addr for addr in db_company.addresses or []}
            new_addresses = []
            
            for addr_data in addresses:
                if addr_data.id and addr_data.id in old_addresses:
                    # Atualiza endereço existente
                    addr_obj = old_addresses.pop(addr_data.id)
                    update_addr_data = addr_data.model_dump(exclude_unset=True)
                    for k, v in update_addr_data.items():
                        setattr(addr_obj, k, v)
                    new_addresses.append(addr_obj)
                else:
                    # Cria novo endereço
                    new_addr = AddressUpdate(**addr_data.model_dump(exclude_unset=True))
                    new_addr.company_id = db_company.id
                    new_addresses.append(new_addr)
            
            # Remove endereços não enviados
            for addr_to_del in old_addresses.values():
                session.delete(addr_to_del)
            
            db_company.addresses = new_addresses
            
        except Exception as e:
            logging.error(f"Erro ao atualizar endereços: {str(e)}", exc_info=True)
            raise AppHttpException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao processar endereços",
                solution="Verifique os dados dos endereços e tente novamente."
            )

    async def chatbot_read_status(self, session: Session = Depends(db_session)) -> StatusResponse:
        """Lê o status atual do chatbot com tratamento robusto"""
        try:
            company = await self._get_company_for_status(session)
            return StatusResponse(
                current_status=company.chatbot_status,
                message=f"Status atual do chatbot: {company.chatbot_status.value}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao ler status do chatbot: {str(e)}", exc_info=True)
            raise AppHttpException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao recuperar status do chatbot",
                solution="Tente novamente mais tarde."
            )

    async def company_read_status(self, session: Session = Depends(db_session)) -> CompanyStatusResponse:
        """Lê o status atual da empresa com tratamento robusto"""
        try:
            company = await self._get_company_for_status(session)
            return CompanyStatusResponse(
                current_status=company.status,
                message=f"Status atual da empresa: {company.status.value}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao ler status da empresa: {str(e)}", exc_info=True)
            raise AppHttpException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao recuperar status da empresa",
                solution="Tente novamente mais tarde."
            )

    async def _get_company_for_status(self, session: Session) -> Company:
        """Método auxiliar para buscar empresa com tratamento de erros"""
        try:
            company = session.exec(select(Company).order_by(Company.updated_at.desc())).first()
            if not company:
                raise AppHttpException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma empresa encontrada",
                    solution="Verifique se a empresa foi corretamente cadastrada."
                )
            return company
        except Exception as e:
            logger.error(f"Erro ao buscar empresa para status: {str(e)}", exc_info=True)
            raise

    async def chatbot_change_status(
        self,
        payload: ChatbotStatusUpdate,
        session: Session = Depends(db_session)
    ) -> StatusResponse:
        """Atualiza o status do chatbot com tratamento completo"""
        try:
            company = await self._get_company_for_status(session)
            
            try:
                company.chatbot_status = payload.new_status
                company.updated_at = datetime.now(timezone.utc)
                session.add(company)
                session.commit()
                session.refresh(company)
                
                return StatusResponse(
                    current_status=company.chatbot_status,
                    message=f"Status do chatbot atualizado para: {company.chatbot_status.value}"
                )
            except Exception as e:
                session.rollback()
                logger.error(f"Erro ao atualizar status do chatbot: {str(e)}", exc_info=True)
                raise AppHttpException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Falha ao persistir alteração de status",
                    solution="Tente novamente mais tarde."
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao alterar status do chatbot: {str(e)}", exc_info=True)
            raise AppHttpException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao alterar status do chatbot",
                solution="Tente novamente mais tarde."
            )

    async def change_company_status(
        self,
        payload: CompanyStatusUpdate,
        session: Session = Depends(db_session)
    ) -> CompanyStatusResponse:
        """Atualiza o status da empresa com tratamento completo"""
        try:
            company = await self._get_company_for_status(session)
            
            try:
                company.status = payload.new_status
                company.updated_at = datetime.now(timezone.utc)
                session.add(company)
                session.commit()
                session.refresh(company)
                
                return CompanyStatusResponse(
                    current_status=company.status,
                    message=f"Status da empresa atualizado para: {company.status.value}"
                )
            except Exception as e:
                session.rollback()
                logger.error(f"Erro ao atualizar status da empresa: {str(e)}", exc_info=True)
                raise AppHttpException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Falha ao persistir alteração de status",
                    solution="Tente novamente mais tarde."
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao alterar status da empresa: {str(e)}", exc_info=True)
            raise AppHttpException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno ao alterar status da empresa",
                solution="Tente novamente mais tarde."
            )