from os import path, unlink
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from typing import BinaryIO

from numpy import frombuffer, int16, float32
from whisper import Whisper, load_model, transcribe

from core.data_access import speech_to_text_log

model: Whisper = load_model("./data/whisperer.pt")
speech_to_text_log.info("Модель распознавания речи была загружена")

def get_text_from_audio_stream(stream: BinaryIO) -> str:
    stream.seek(0)
    try:
        with NamedTemporaryFile(suffix='.mp4', mode="wb", delete=False) as temp_video_file:
            temp_video_path = temp_video_file.name
            temp_video_file.write(stream.read())

        ffmpeg_cmd = [
            'ffmpeg', '-i', temp_video_path, '-f', 'wav',
            '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000',
            '-vn', '-y', '-loglevel', 'quiet', 'pipe:1'
        ]

        process = Popen(ffmpeg_cmd, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise Exception(f"FFmpeg error: {stderr}")

        result = frombuffer(stdout[44:], dtype=int16).astype(float32) / 32768.0
        success = True
    except Exception as e:
        speech_to_text_log.error(f"Ошибка извлечения аудио: {e}")
        success = False
    finally:
        if path.exists(temp_video_path):
            unlink(temp_video_path)

    if not success:
        return ""

    result = transcribe(model=model, audio=result, language="ru")
    return result["text"]