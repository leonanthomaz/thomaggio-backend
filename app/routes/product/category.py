from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, update
from app.models.product.category import Category
from app.models.product.product import Product
from app.models.user.user import User
from app.auth.auth import AuthRouter
from app.database.connection import get_session
from app.schemas.product.category import CategoryCreate, CategoryUpdate

db_session = get_session
get_current_user = AuthRouter().get_current_user

class CategoryRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/categories/", self.get_all_categories, methods=["GET"], response_model=List[Category])
        self.add_api_route("/categories/", self.create_category, methods=["POST"], response_model=Category)
        self.add_api_route("/categories/{category_id}", self.get_category_by_id, methods=["GET"], response_model=Category)
        self.add_api_route("/categories/{category_id}", self.update_category_by_id, methods=["PUT"], response_model=Category)
        self.add_api_route("/categories/{category_id}", self.delete_category_by_id, methods=["DELETE"], response_model=dict)

    def get_all_categories(self, session: Session = Depends(db_session)):
        categories = session.query(Category).all()
        return categories

    def create_category(self, category_request: CategoryCreate, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        category = Category(
            name=category_request.name,
            description=category_request.description,
            is_active=category_request.is_active,
            allowed_types=category_request.allowed_types
        )
        session.add(category)
        session.commit()
        session.refresh(category)
        return category

    def get_category_by_id(self, category_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")
        return category

    def update_category_by_id(self, category_id: int, updated_category: CategoryUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")

        for key, value in updated_category.dict(exclude_unset=True).items():
            setattr(category, key, value)

        category.updated_at = datetime.now(timezone.utc)
        session.add(category)

        if updated_category.is_active is False:
            session.exec(
                update(Product)
                .where(Product.category_id == category_id)
                .values(is_active=False, deactivated_by_category=True)
            )
        elif updated_category.is_active is True:
            session.exec(
                update(Product)
                .where(Product.category_id == category_id, Product.deactivated_by_category == True)
                .values(is_active=True, deactivated_by_category=False)
            )


        session.commit()
        session.refresh(category)
        return category

    def delete_category_by_id(self, category_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(db_session)):
        category = session.get(Category, category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada")

        session.delete(category)
        session.commit()
        return {"message": "Categoria deletada com sucesso"}
