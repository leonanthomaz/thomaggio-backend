from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from app.models.address import Address
from app.models.company import Company
from app.schemas.address import AddressUpdate
from app.schemas.chat_status import ChatbotStatusUpdate, StatusResponse
from app.schemas.company import CompanyStatusResponse, CompanyStatusUpdate, CompanyUpdate
from app.database.connection import get_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
db_session = get_session

class CompanyRouter(APIRouter):
    """
    Roteador para operações relacionadas a empresas.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.add_api_route("/company", self.get_company, methods=["GET"], response_model=Company)
        
        self.add_api_route("/company/status", self.company_read_status, methods=["GET"], response_model=CompanyStatusResponse)
        self.add_api_route("/company/status", self.change_company_status, methods=["POST"], response_model=CompanyStatusResponse)
        
        self.add_api_route("/company/chatbot-status", self.chatbot_read_status, methods=["GET"], response_model=StatusResponse)
        self.add_api_route("/company/chatbot-status", self.chatbot_change_status, methods=["POST"], response_model=StatusResponse)
        
        self.add_api_route("/company/{company_id}", self.update_company, methods=["PUT"], response_model=Company)

    def get_company(self, session: Session = Depends(db_session)):
        """
        Retorna os dados de uma empresa cadastrada pelo ID.
        """
        company = session.exec(select(Company).where(Company.id == 1)).first()
        if not company:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empresa não encontrada.")
        return company

    def update_company(self, company: CompanyUpdate, session: Session = Depends(db_session)):
        db_company = session.exec(select(Company).where(Company.id == 1)).first()
        
        if not db_company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Atualiza campos simples
        update_data = company.model_dump(exclude_unset=True, exclude={"addresses"})
        for key, value in update_data.items():
            setattr(db_company, key, value)

        # Atualiza endereços
        if company.addresses is not None:
            old_addresses = {addr.id: addr for addr in db_company.addresses or []}
            new_addresses = []
            
            for addr_data in company.addresses:
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

        db_company.updated_at = datetime.now(timezone.utc)
        session.add(db_company)
        session.commit()
        session.refresh(db_company)
        
        return db_company

    async def chatbot_read_status(self, session: Session = Depends(db_session)) -> StatusResponse:
        """Lê o status atual do chatbot"""
        try:
            company = session.exec(
                select(Company).order_by(Company.updated_at.desc())
            ).first()

            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma empresa encontrada para obter o status do chatbot."
                )

            return StatusResponse(
                current_status=company.chatbot_status,
                message=f"Status atual do chatbot: {company.chatbot_status.value}"
            )

        except Exception as e:
            logging.exception("Erro ao ler o status do chatbot")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao recuperar o status do chatbot"
            )
        finally:
            session.close()

    async def company_read_status(self, session: Session = Depends(db_session)) -> CompanyStatusResponse:
        """Lê o status atual do chatbot"""
        try:
            company = session.exec(
                select(Company).order_by(Company.updated_at.desc())
            ).first()

            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma empresa encontrada para obter o status do chatbot."
                )

            return CompanyStatusResponse(
                current_status=company.status,
                message=f"Status atual da empresa: {company.status.value}"
            )

        except Exception as e:
            logging.exception("Erro ao ler o status da empresa")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao recuperar o status da empresa"
            )
        finally:
            session.close()
            
    async def chatbot_change_status(
        self,
        payload: ChatbotStatusUpdate,
        session: Session = Depends(db_session)
    ) -> StatusResponse:
        """Atualiza o status operacional do chatbot"""
        try:
            company = session.exec(
                select(Company).order_by(Company.updated_at.desc())
            ).first()

            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Nenhuma empresa encontrada para atualizar o status do chatbot."
                )

            company.chatbot_status = payload.new_status
            company.updated_at = datetime.now(timezone.utc)

            session.add(company)
            session.commit()
            session.refresh(company)

            return StatusResponse(
                current_status=company.chatbot_status,
                message=f"Status do chatbot atualizado para: {company.chatbot_status.value}"
            )

        except Exception:
            session.rollback()
            logging.exception("Erro ao atualizar o status do chatbot")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao atualizar o status do chatbot"
            )
        finally:
            session.close()

    async def change_company_status(
        self,
        payload: CompanyStatusUpdate,
        session: Session = Depends(db_session)
    ) -> CompanyStatusResponse:
        """Atualiza o status operacional da empresa (aberto, fechado, manutenção)."""
        try:
            company = session.exec(
                select(Company).where(Company.id == 1)
            ).first()

            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Empresa não encontrada."
                )

            company.status = payload.new_status
            company.updated_at = datetime.now(timezone.utc)

            session.add(company)
            session.commit()
            session.refresh(company)

            return CompanyStatusResponse(
                current_status=company.status,
                message=f"Status da empresa atualizado para: {company.status.value}"
            )

        except Exception:
            session.rollback()
            logging.exception("Erro ao atualizar o status da empresa")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao atualizar o status da empresa"
            )
        finally:
            session.close()
