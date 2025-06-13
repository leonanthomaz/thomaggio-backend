from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models.product.product import Product
from app.models.supply.product_supply import ProductSupply
from app.models.supply.supply import Supply
from app.schemas.supply.product_supply import ProductSupplyCreate, ProductSupplyUpdate, ProductSupplyRead, ProductWithSuppliesRead
from app.database.connection import get_session

db_session = get_session

class ProductSupplyRouter(APIRouter):
    """
    Roteador para operações relacionadas a ProductSupply (Relação entre produtos e insumos).
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_api_route("/product_supply", self.create_product_supply, methods=["POST"], response_model=ProductSupplyRead)
        self.add_api_route("/product_supply/{product_supply_id}", self.get_product_supply, methods=["GET"], response_model=ProductSupplyRead)
        self.add_api_route("/product_supply/{product_supply_id}", self.update_product_supply, methods=["PUT"], response_model=ProductSupplyRead)
        self.add_api_route("/product_supply/{product_supply_id}", self.delete_product_supply, methods=["DELETE"])
        self.add_api_route("/product_supplies", self.list_product_supplies, methods=["GET"], response_model=list[ProductSupplyRead])
        self.add_api_route(
                    "/products_with_supplies",
                    self.list_products_with_supplies,
                    methods=["GET"],
                    response_model=list[ProductWithSuppliesRead]
                )
    def create_product_supply(self, product_supply: ProductSupplyCreate, session: Session = Depends(db_session)):
        # Verificar se o produto e o insumo existem
        product = session.get(Product, product_supply.product_id)
        supply = session.get(Supply, product_supply.supply_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Produto não encontrado.")
        if not supply:
            raise HTTPException(status_code=404, detail="Insumo não encontrado.")

        # Criação da relação ProductSupply
        new_product_supply = ProductSupply(**product_supply.dict())
        session.add(new_product_supply)
        session.commit()
        session.refresh(new_product_supply)
        
        # Retornar o schema completo com os nomes
        return ProductSupplyRead(
            id=new_product_supply.id,
            product_id=new_product_supply.product_id,
            product_name=product.name,
            supply_id=new_product_supply.supply_id,
            supply_name=supply.name,
            quantity=new_product_supply.quantity,
            unit=new_product_supply.unit,
            created_at=new_product_supply.created_at
        )
        
    def get_product_supply(self, product_supply_id: int, session: Session = Depends(db_session)):
        product_supply = session.get(ProductSupply, product_supply_id)
        if not product_supply:
            raise HTTPException(status_code=404, detail="Relação Produto-Insumo não encontrada.")
        return product_supply

    def update_product_supply(self, product_supply_id: int, product_supply_data: ProductSupplyUpdate, session: Session = Depends(db_session)):
        product_supply = session.get(ProductSupply, product_supply_id)
        if not product_supply:
            raise HTTPException(status_code=404, detail="Relação Produto-Insumo não encontrada.")

        for key, value in product_supply_data.dict(exclude_unset=True).items():
            setattr(product_supply, key, value)

        product_supply.updated_at = datetime.now(timezone.utc)

        session.add(product_supply)
        session.commit()
        session.refresh(product_supply)

        return product_supply

    def delete_product_supply(self, product_supply_id: int, session: Session = Depends(db_session)):
        product_supply = session.get(ProductSupply, product_supply_id)
        if not product_supply:
            raise HTTPException(status_code=404, detail="Relação Produto-Insumo não encontrada.")

        session.delete(product_supply)
        session.commit()
        return {"detail": "Relação Produto-Insumo deletada com sucesso."}

    def list_product_supplies(self, session: Session = Depends(db_session)):
        product_supplies = session.exec(select(ProductSupply)).all()
        return product_supplies

    def list_products_with_supplies(self, session: Session = Depends(db_session)):
        products = session.exec(select(Product)).all()
        product_data = []

        for product in products:
            supplies = session.exec(
                select(ProductSupply)
                .where(ProductSupply.product_id == product.id)
                .join(Supply)
            ).all()

            supplies_data = []
            total_cost = 0.0

            for ps in supplies:
                supply = session.get(Supply, ps.supply_id)
                supply_cost = (supply.unit_price or 0) * ps.quantity
                total_cost += supply_cost

                supplies_data.append({
                    "id": ps.supply_id,
                    "name": supply.name,
                    "unit_price": supply.unit_price,
                    "quantity": ps.quantity,
                    "unit": ps.unit,
                    "cost": supply_cost
                })

            product_data.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "supplies": supplies_data,
                "total_cost": round(total_cost, 2)
            })

        return product_data