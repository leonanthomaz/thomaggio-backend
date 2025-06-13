from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
import os

from app.configuration.settings import Configuration
from app.database.connection import get_session
from app.models.company.company import Company
from app.models.user.user import User
from app.schemas.auth.auth import EmailResetRequest, PasswordResetRequest, Token, AuthCredentials
from app.email import EmailService

configuration = Configuration()

SECRET_KEY = os.getenv("SECRET_KEY", "UmaVezFlamengoSempreFlamengo")
# JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

JWT_EXPIRATION_HOURS=configuration.jwt_expiration_hours

db_session = get_session
email_service = EmailService()


class AuthRouter(APIRouter):
    def __init__(self):
        super().__init__()
        self.add_api_route("/login", self.login, methods=["POST"], response_model=Token)
        self.add_api_route("/me", self.me, methods=["GET"])
        self.add_api_route("/validate-email", self.validate_email, methods=["POST"])
        self.add_api_route("/reset-password", self.reset_password, methods=["POST"])

    def _generate_jwt(self, user_id: int) -> str:
        expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
        payload = {"user_id": user_id, "exp": expiration}
        return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    def decode_jwt(self, token: str) -> dict:
        try:
            return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Token inválido")

    def get_token_expiration(self, payload: dict) -> datetime:
        exp = payload.get("exp")
        return datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)

    def get_current_user(self, request: Request, session: Session = Depends(db_session)) -> User:
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=401, detail="Acesso não autorizado")

        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Formato de autenticação inválido")

        token = parts[1]
        payload = self.decode_jwt(token)
        user = session.get(User, payload["user_id"])

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return user

    def login(self, credentials: AuthCredentials, session: Session = Depends(db_session)):
        user = session.exec(select(User).where(User.username == credentials.username)).first()

        if not user or not bcrypt.checkpw(credentials.password.encode(), user.password_hash.encode()):
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

        if user.role not in ["employee", "admin"]:
            raise HTTPException(status_code=403, detail="Acesso restrito ao sistema de gerenciamento")

        token = self._generate_jwt(user.id)
        return Token(token=token)

    def me(self, request: Request, session: Session = Depends(db_session)):  # Recebe a Request
        user = self.get_current_user(request, session)  # Passa o request inteiro
        company = session.get(Company, user.company_id)

        if not company:
            raise HTTPException(status_code=404, detail="Empresa não encontrada")

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "username": user.username,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
                "last_login": user.last_login,
                "addresses": [a.model_dump() for a in user.addresses] if user.addresses else [],
                "is_admin": user.is_admin,
            },
            "company": {
                "id": company.id,
                "name": company.name,
                "description": company.description,
                "industry": company.industry,
                "cnpj": company.cnpj,
                "phone": company.phone,
                "addresses": [a.model_dump() for a in company.addresses] if company.addresses else [],
                "status": company.status,
                "opening_time": company.opening_time,
                "closing_time": company.closing_time,
                "working_days": company.working_days,
                "contact_email": company.contact_email,
                "privacy_policy_version": company.privacy_policy_version,
                "logo_url": company.logo_url,
                "created_at": company.created_at,
                "updated_at": company.updated_at,
                "deleted_at": company.deleted_at,
            }
        }
    
    def validate_email(self, data: EmailResetRequest, background_tasks: BackgroundTasks, session: Session = Depends(db_session)):
        user = session.exec(select(User).where(User.email == data.email)).first()

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        token = self._generate_jwt(user.id)
        user.token_password_reset = token
        session.commit()

        reset_link = f"https://thomaggio.vercel.app/change-password/{token}"
        email_service.send_validate_email(email=user.email, link=reset_link, background_tasks=background_tasks)

        return {"message": "Link de validação enviado para o email", "token": token}

    def reset_password(self, password_request: PasswordResetRequest, session: Session = Depends(db_session)):
        payload = self.decode_jwt(password_request.token)
        user = session.get(User, payload["user_id"])

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        if self.get_token_expiration(payload) < datetime.now(tz=timezone.utc):
            user.token_password_reset = None
            session.commit()
            raise HTTPException(status_code=400, detail="O token de redefinição de senha expirou. Solicite um novo.")

        hashed = bcrypt.hashpw(password_request.password.encode(), bcrypt.gensalt()).decode()
        user.password_hash = hashed
        user.token_password_reset = None
        session.commit()

        return {"message": "Senha redefinida com sucesso"}
