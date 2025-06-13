from fastapi import HTTPException, status
from app.models.user.user import User

def is_admin(user: User):
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Acesso negado")