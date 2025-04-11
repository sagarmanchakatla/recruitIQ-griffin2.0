FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app/ ./streamlit_app/
WORKDIR /app/streamlit_app

EXPOSE 8501

EXPOSE 8501
CMD ["streamlit", "run", "mainapp.py", "--server.port=8501", "--server.address=0.0.0.0"]
