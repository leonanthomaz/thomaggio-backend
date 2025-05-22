import os
import uuid
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form
from sqlmodel import Session
from app.models.product import Product
from app.models.category import Category
from app.models.user import User
from app.auth.auth import AuthRouter
from app.database.connection import get_session
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

db_session = get_session
get_current_user = AuthRouter().get_current_user

PRODUCT_IMAGE_DIR = "app/assets/img/product"
os.makedirs(PRODUCT_IMAGE_DIR, exist_ok=True)


class ProductRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_api_route("/products/", self.list_products, methods=["GET"], response_model=List[ProductResponse])
        self.add_api_route("/products/", self.create_product, methods=["POST"], response_model=ProductResponse)
        self.add_api_route("/products/{product_id}", self.get_product, methods=["GET"], response_model=ProductResponse)
        self.add_api_route("/products/{product_id}", self.update_product, methods=["PUT"], response_model=ProductResponse)
        self.add_api_route("/products/{product_id}", self.delete_product, methods=["DELETE"], response_model=dict)
        self.add_api_route("/products/{product_id}/image", self.update_product_image, methods=["POST"], response_model=ProductResponse)

    def get_product(self, product_id: int, session: Session = Depends(db_session)):
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
        return product

    async def create_product(
        self,
        name: str = Form(...),
        description: Optional[str] = Form(None),
        price: float = Form(...),
        category_id: Optional[int] = Form(None),
        image_file: Optional[UploadFile] = None,
        rating: Optional[float] = Form(0.0),
        reviews_count: Optional[int] = Form(0),
        size: Optional[str] = Form(None),
        selected_flavors: Optional[str] = Form(None),
        attributes: Optional[str] = Form(None),
        prices_by_size: Optional[str] = Form(None),
        is_active: bool = Form(True),
        current_user: User = Depends(get_current_user),
        session: Session = Depends(db_session),
    ):
        category = None
        if category_id:
            category = session.get(Category, category_id)
            if not category:
                raise HTTPException(status_code=400, detail="Categoria não encontrada")

        image_filename = None
        if image_file:
            try:
                file_extension = image_file.filename.split(".")[-1].lower()
                image_filename = f"{uuid.uuid4().hex}.{file_extension}"
                file_path = os.path.join(PRODUCT_IMAGE_DIR, image_filename)

                with open(file_path, "wb") as image_data:
                    contents = await image_file.read()
                    image_data.write(contents)
            except Exception as e:
                raise HTTPException(500, detail=f"Erro ao salvar a imagem: {e}")

        # Parse dos atributos
        parsed_attributes = None
        try:
            if attributes:
                parsed_attributes = json.loads(attributes)
                if not all(isinstance(v, list) for v in parsed_attributes.values()):
                    raise ValueError("Todos os valores de attributes devem ser listas.")
        except Exception as e:
            logging.exception("Erro ao interpretar attributes")
            raise HTTPException(400, detail=f"Atributos inválidos: {e}")

        # Parse dos tamanhos
        parsed_size = None
        try:
            if size:
                parsed_size = json.loads(size)
                if not isinstance(parsed_size, list):
                    raise ValueError("size deve ser uma lista.")
                if not all(isinstance(item, str) for item in parsed_size):
                    raise ValueError("Todos os itens de size devem ser strings.")
        except Exception as e:
            logging.exception("Erro ao interpretar size")
            raise HTTPException(400, detail=f"Tamanhos inválidos: {e}")
        
        # Parse dos sabores
        parsed_flavors = None
        try:
            if selected_flavors:
                parsed_flavors = json.loads(selected_flavors)
                if not isinstance(parsed_flavors, list):
                    raise ValueError("flavors deve ser uma lista.")
                if not all(isinstance(item, str) for item in parsed_flavors):
                    raise ValueError("Todos os itens de flavors devem ser strings.")
        except Exception as e:
            logging.exception("Erro ao interpretar flavors")
            raise HTTPException(400, detail=f"Sabores inválidos: {e}")


        # Parse dos preços por tamanho
        parsed_prices = None
        try:
            if prices_by_size:
                parsed_prices = json.loads(prices_by_size)
                if not isinstance(parsed_prices, dict):
                    raise ValueError("prices_by_size deve ser um dicionário.")
                if not all(isinstance(v, (int, float)) for v in parsed_prices.values()):
                    raise ValueError("Todos os valores de prices_by_size devem ser numéricos.")
        except Exception as e:
            logging.exception("Erro ao interpretar prices_by_size")
            raise HTTPException(400, detail=f"Preços por tamanho inválidos: {e}")

        product_data = ProductCreate(
            name=name,
            description=description,
            price=price,
            category_id=category_id,
            image=image_filename,
            rating=rating,
            reviews_count=reviews_count,
            attributes=parsed_attributes,
            size=parsed_size,
            selected_flavors=parsed_flavors,
            prices_by_size=parsed_prices,
            is_active=is_active,
            company_id=current_user.company_id,
            type="geral",
        )

        product = Product.from_orm(product_data)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    def list_products(self, session: Session = Depends(db_session)):
        return session.query(Product).all()

    async def update_product(
        self,
        product_id: int,
        product_update: ProductUpdate,
        session: Session = Depends(db_session),
    ):
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

        product_data = product_update.dict(exclude_unset=True)
        for key, value in product_data.items():
            setattr(product, key, value)

        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    async def update_product_image(
        self,
        product_id: int,
        image_file: UploadFile = Form(...),
        session: Session = Depends(db_session),
    ):
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

        if product.image:
            old_image_path = os.path.join(PRODUCT_IMAGE_DIR, product.image)
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        try:
            file_extension = image_file.filename.split(".")[-1].lower()
            image_filename = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(PRODUCT_IMAGE_DIR, image_filename)

            with open(file_path, "wb") as image_data:
                contents = await image_file.read()
                image_data.write(contents)

            product.image = image_filename
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao salvar/atualizar a imagem: {e}",
            )

    def delete_product(self, product_id: int, session: Session = Depends(db_session)):
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

        product.is_active = False
        session.add(product)
        session.commit()
        session.refresh(product)
        return {"message": f"Produto com ID {product_id} inativado com sucesso"}