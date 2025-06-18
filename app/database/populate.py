from datetime import datetime, time, timezone
import bcrypt
from sqlmodel import Session, select
from app.enums.company_status import CompanyStatus
from app.models import Company, User, Category, Product
from app.configuration.settings import Configuration
from app.models.user.address import Address
from app.models.company.delivery_config import DeliveryConfig
from app.schemas.company.delivery_config import DeliveryConfigCreate

# Carregar configuração global
configuration = Configuration()

def populate_database(session: Session):
    """Inicializa o banco de dados e popula com dados iniciais."""
    company = populate_company(session)
    populate_admin_user(session, company_id=company.id)
    populate_employee_user(session, company_id=company.id)
    populate_default_category(session)
    populate_products(session, company_id=company.id)
    populate_delivery_config(session)

def populate_company(session: Session) -> Company:
    """Cria a empresa principal, se ainda não existir."""
    company_data = {
        "name": "Thomaggio",
        "description": "Pizzaria Thomaggio, a melhor pizza da cidade",
        "industry": "Pizzaria",
        "cnpj": "12.345.678/0001-99",
        "phone": "(21) 99835-9326",
        "website": "https://thomaggio.vercel.app",
        "opening_time": time(18, 0),
        "closing_time": time(23, 0),
        "working_days": ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"],
        "status": CompanyStatus.OPEN,
        "privacy_policy_version": "1.0.0",
        "contact_email": "contato@thomaggio.com",
        "logo_url": "https://thomaggio.vercel.app/logo.png",
        "social_media_links": {
            "facebook": "https://facebook.com/thomaggio",
            "instagram": "https://instagram.com/thomaggio"
        },
    }

    company = session.exec(select(Company).where(Company.name == company_data["name"])).first()
    if not company:
        company = Company(**company_data)
        session.add(company)
        session.commit()
        session.refresh(company)
    return company

def populate_delivery_config(session: Session):
    """Cria configuração de entrega padrão, se ainda não existir."""
    existing_config = session.exec(select(DeliveryConfig)).first()
    if existing_config:
        return

    config_data = DeliveryConfigCreate(
        cep="20531402",
        central_point_lat=-22.9444,
        central_point_lng=-43.2902,
        radius=12.0,
        default_delivery_fee=5.0
    )

    config = DeliveryConfig(**config_data.dict())
    session.add(config)
    session.commit()
    session.refresh(config)

def populate_admin_user(session: Session, company_id: int):
    """Cria o usuário admin padrão, se ainda não existir."""
    admin_username = "leonanthomaz"
    user = session.exec(select(User).where(User.username == admin_username)).first()
    if not user:
        user_data = {
            "name": "Leonan",
            "username": admin_username,
            "email": "leonan.thomaz@gmail.com",
            "company_id": company_id,
            "password_hash": hash_password("leonan2knet"),
            "phone": "21998090928",
            "role": "admin",
            "is_admin": True,
            "is_active": True,
        }
        user = User(**user_data)
        session.add(user)
        session.commit()
        session.refresh(user)
        
        address_data = Address(
            user_id=user.id,
            street="Rua Antonio Nunes",
            company_id=1,
            number="1",
            complement="F",
            neighborhood="Alto da Boa Vista",
            reference="Próximo ao Parque Nacional da Tijuca",
            city="Rio de Janeiro",
            state="RJ",
            zip_code="20531-402",
            is_company_address= True
        )
        
        session.add(address_data)
        session.commit()
        
def populate_employee_user(session: Session, company_id: int):
    """Cria um usuário funcionário padrão, se ainda não existir."""
    employee_username = "luziathomaz"
    user = session.exec(select(User).where(User.username == employee_username)).first()
    if not user:
        user_data = {
            "name": "Luzia",
            "username": employee_username,
            "email": "luzia.ts.rj@gmail.com",
            "company_id": company_id,
            "password_hash": hash_password("123"),
            "phone": "21996416049",
            "role": "employee",
            "is_admin": False,
            "is_active": True,
        }
        user = User(**user_data)
        session.add(user)
        session.commit()
        session.refresh(user)

        address_data = Address(
            user_id=user.id,
            company_id=company_id,
            street="Rua do Funcionário",
            number="123",
            complement="Casa",
            neighborhood="Centro",
            reference="Próximo à praça",
            city="Rio de Janeiro",
            state="RJ",
            zip_code="20531-390",
            is_company_address=False
        )

        session.add(address_data)
        session.commit()

def populate_default_category(session: Session):
    """Cria a categoria padrão 'Geral' se ela ainda não existir."""
    existing = session.exec(select(Category)).all()

    if not existing:
        categories = [
            # default_category,
            Category(
                name="Salgados",
                description="Nossas melhores salgados",
                is_active=True,
                allowed_types=["misto", "premium"],
                created_at=datetime.now(timezone.utc),
            ),
            Category(
                name="Pizzas",
                description="Nossas pizzas mais pedidas",
                is_active=True,
                allowed_types=["salgada", "doce"],
                created_at=datetime.now(timezone.utc),
            ),
            Category(
                name="Bebidas",
                description="Bebidas geladas para acompanhar",
                is_active=True,
                allowed_types=["refrigerante", "suco", "cerveja"],
                created_at=datetime.now(timezone.utc),
            ),
        ]
        session.add_all(categories)
        session.commit()

def populate_products(session: Session, company_id: int):
    """Popula produtos fictícios para testes."""
    existing_products = session.exec(select(Product)).all()
    
    if existing_products:
        return

    # Pega categorias pelo nome
    categorias = {
        cat.name: cat for cat in session.exec(select(Category)).all()
    }

    produtos = [
        Product(
            name="Pizza de Calabresa",
            description="Molho de tomate, calabresa, mussarela e manjericão fresco",
            stock=10,
            image="ad1b6ba4025a4145b2faa1a1404e8dad.jpg",
            size=["M", "G"],
            prices_by_size={"M": 42.0, "G": 55.0},
            types=["salgada"],
            rating=4.8,
            reviews_count=10,
            is_active=True,
            company_id=company_id,
            category=categorias.get("Pizzas"),
            flavors_required=False,
            options_required=False
        ),
        Product(
            name="Pizza de Mussarela",
            description="Molho de tomate, mussarela, orégano e azeite",
            stock=5,
            image="7765a63ad9a84abdb76f2834837ae0df.png",
            size=["M", "G"],
            prices_by_size={"M": 45.0, "G": 58.0},
            types=["salgada"],
            rating=4.6,
            reviews_count=32,
            is_active=True,
            company_id=company_id,
            category=categorias.get("Pizzas"),
            flavors_required=False,
            options_required=False
        ),
        Product(
            name="Pizza de Chocolate",
            description="Brigadeiro e morango",
            stock=5,
            image="e4280933dcca4264a8b46bcaf9c7491a.jpg",
            size=["M", "G"],
            prices_by_size={"M": 45.0, "G": 58.0},
            types=["doce"],
            rating=4.6,
            reviews_count=32,
            is_active=True,
            company_id=company_id,
            category=categorias.get("Pizzas"),
            flavors_required=False,
            options_required=False
        ),
        Product(
            name="Coca-Cola 2L",
            description="Bebida gelada",
            stock=20,
            image="50e2c708d2dc49398646a9e272f1741a.jpg",
            size=["U"],
            prices_by_size={"U": 13.0},
            types=["refrigerante"],
            rating=4.9,
            reviews_count=150,
            is_active=True,
            company_id=company_id,
            category=categorias.get("Bebidas"),
            flavors_required=False,
            options_required=False

        ),
        Product(
            name="Guaraná Antártica",
            description="Bebida gelada",
            stock=20,
            image="a16294bdf9dc46dbb48c17facd5b3c07.webp",
            size=["U"],
            prices_by_size={"U": 11.0},
            types=["refrigerante"],
            rating=4.9,
            reviews_count=150,
            is_active=True,
            company_id=company_id,
            category=categorias.get("Bebidas"),
            flavors_required=False,
            options_required=False
        ),
        Product(
            name="Porção de 40 salgadinhos",
            description="Melhores salgadinhos",
            image="0225dc112e384a6a969d1e8a56255558.webp",
            size=["U"],
            selected_flavors= ["Coxinha", "Risole de Carne", "Enroladinho", "Kibe", "Bolinha de Queijo"],
            prices_by_size={"U": 36.0},
            types=["misto"],
            rating=4.9,
            reviews_count=25,
            is_active=True,
            company_id=company_id,
            category=categorias.get("Salgados"),
            min_flavors=3,
            max_flavors=5,
            flavors_required=True,
            options_required=False

        ),
        Product(
            name="Porção de 50 salgadinhos",
            description="Melhores salgadinhos",
            image="814e3b9c57184a0399456dab235a3b0a.jpg",
            size=["U"],
            selected_flavors= ["Coxinha", "Risole de Carne", "Risole de Palmito", "Kibe", "Queijo com Presunto"],
            prices_by_size={"U": 45.0},
            types=["misto"],
            rating=4.9,
            reviews_count=31,
            is_active=True,
            company_id=company_id,
            category=categorias.get("Salgados"),
            min_flavors=5,
            max_flavors=10,
            flavors_required=True,
            options_required=False
        ),
    ]

    session.add_all(produtos)
    session.commit()
    
def hash_password(password: str) -> str:
    """Gera um hash seguro para senha usando bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
