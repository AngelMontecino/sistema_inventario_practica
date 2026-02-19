FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo
COPY . .

# puerto
EXPOSE 8002

# comando para ejecutar servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]
