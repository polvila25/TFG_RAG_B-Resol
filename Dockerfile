FROM python:3.10-slim

# Establir directori de treball
WORKDIR /app

# Copiar el fitxer de requeriments
COPY requirements.txt .

# Instal·lar les dependències del sistema necessàries (gcc etc. si calen per llibreries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Instal·lar els requeriments de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el codi font
COPY src/ src/
COPY frontend/ frontend/
COPY data/ data/
COPY assets/ assets/

# Exposar el port de Streamlit
EXPOSE 8501

# Variables d'entorn per defecte per a Streamlit
ENV PYTHONUNBUFFERED=1

# Comanda per executar l'aplicació
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
