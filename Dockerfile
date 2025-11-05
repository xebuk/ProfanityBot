FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p data

COPY code/data_processing.py .
COPY code/textutil.py .
COPY code/database.py .
COPY code/main.py .

CMD ["python", "main.py"]