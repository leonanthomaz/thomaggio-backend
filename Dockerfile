FROM python:3.11-slim

# Instalar dependências do sistema necessárias para o psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

# Definir diretório de trabalho
WORKDIR /app

# Copiar o código do projeto
COPY . .

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Expor porta
EXPOSE 5000

# Comando de inicialização
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]