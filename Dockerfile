FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY textutil.py .
COPY database.py .
RUN mkdir -p data
COPY main.py .

CMD ["python", "main.py"]