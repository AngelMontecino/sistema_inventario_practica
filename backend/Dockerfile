FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .

# puerto
EXPOSE 8001

# comando para ejecutar servidor
CMD ["fastapi", "dev", "app/main.py", "--host", "0.0.0.0", "--port", "8001"]
