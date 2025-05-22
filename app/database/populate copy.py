# from datetime import time
# import bcrypt
# from sqlmodel import Session, select
# from app.models import Company, User, Category
# from app.configuration.settings import Configuration
# from app.models.address import Address

# # Carregar configuração global
# configuration = Configuration()

# def populate_database(session: Session):
#     """Inicializa o banco de dados e popula com dados iniciais."""
#     company = populate_company(session)
#     populate_admin_user(session, company_id=company.id)
#     populate_default_category(session)

# def populate_company(session: Session) -> Company:
#     """Cria a empresa principal, se ainda não existir."""
#     company_data = {
#         "name": "Thomaggio",
#         "description": "Pizzaria Thomaggio, a melhor pizza da cidade",
#         "industry": "Pizzaria",
#         "cnpj": "12.345.678/0001-99",
#         "phone": "(21) 99809-0928",
#         "website": "https://thomaggio.vercel.app",
#         "opening_time": time(18, 0),
#         "closing_time": time(23, 0),
#         "working_days": ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"],
#         "status": "active",
#         "contact_email": "contato@thomaggio.com",
#         "logo_url": "https://thomaggio.vercel.app/logo.png",
#         "social_media_links": {
#             "facebook": "https://facebook.com/thomaggio",
#             "instagram": "https://instagram.com/thomaggio"
#         },
#     }

#     company = session.exec(select(Company).where(Company.name == company_data["name"])).first()
#     if not company:
#         company = Company(**company_data)
#         session.add(company)
#         session.commit()
#         session.refresh(company)
#     return company

# def populate_admin_user(session: Session, company_id: int):
#     """Cria o usuário admin padrão, se ainda não existir."""
#     admin_username = "leonanthomaz"
#     user = session.exec(select(User).where(User.username == admin_username)).first()
#     if not user:
#         user_data = {
#             "name": "Leonan Thomaz",
#             "username": admin_username,
#             "email": "leonan.thomaz@gmail.com",
#             "company_id": company_id,
#             "password_hash": hash_password("leonan2knet"),
#             "phone": "(21) 99809-0928",
#             "role": "admin",
#             "is_admin": True,
#             "is_active": True
#         }
#         user = User(**user_data)
#         session.add(user)
#         session.commit()
#         session.refresh(user)
        
#         address_data = Address(
#             user_id=user.id,
#             street="Rua Antonio Nunes",
#             company_id=1,
#             number="1",
#             complement="B",
#             neighborhood="Alto da Boa Vista",
#             reference="Próximo ao Parque Nacional da Tijuca",
#             city="Rio de Janeiro",
#             state="RJ",
#             zip_code="20531-402"
#         )
        
#         session.add(address_data)
#         session.commit()

# def populate_default_category(session: Session):
#     """Cria a categoria padrão 'Geral' se ela ainda não existir."""
#     category = session.exec(select(Category).where(Category.name == "Geral")).first()
#     if not category:
#         default_category = Category(
#             name="Geral",
#             description="Categoria padrão para produtos sem categoria definida",
#             is_active=True,
#         )
#         session.add(default_category)
#         session.commit()
#         session.refresh(default_category)

# def hash_password(password: str) -> str:
#     """Gera um hash seguro para senha usando bcrypt."""
#     return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
