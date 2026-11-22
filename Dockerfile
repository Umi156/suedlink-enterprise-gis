FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgdal-dev g++ curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY webgis/ ./webgis/
COPY data/webgis_snapshot/ ./data/webgis_snapshot/
EXPOSE 8501 8000
CMD ["streamlit", "run", "webgis/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
