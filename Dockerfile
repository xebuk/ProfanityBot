from python:3.11-slim

workdir /app

copy requirements.txt .
run pip install --no-cache-dir -r requirements.txt
run apt-get update && apt-get install -y ffmpeg

run mkdir -p data
run mkdir -p media

copy core/main.py .
copy core/logs.py .
copy core/database.py .
copy core/speech_recognition.py .
copy core/textutil.py .

copy media media

copy data/chats_with_curse.db data
copy data/curses.txt data
copy data/log.txt data
copy data/normal_words.txt data
copy data/profanity_pipeline.joblib data
copy data/large-v3.pt data
copy data/warnings.txt data

cmd ["python", "main.py"]