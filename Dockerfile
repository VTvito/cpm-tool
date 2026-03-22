FROM python:3.13-slim-bookworm

WORKDIR /app

# Nessuna dipendenza di sistema aggiuntiva necessaria (kaleido non usato in questo branch)
# I grafici Plotly restano interattivi nel browser; i PDF vengono generati senza immagini embedded.

# Dipendenze Python (layer cachato separato dal codice)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Codice sorgente (data/ esclusa via .dockerignore: verrà montata dal volume Fly.io)
COPY . .

EXPOSE 8501

# mkdir -p data/ assicura che la directory esista se il volume non è ancora montato
CMD ["sh", "-c", "mkdir -p /app/data && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
