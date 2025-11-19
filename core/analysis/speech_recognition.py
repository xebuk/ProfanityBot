import os
from tempfile import NamedTemporaryFile
from subprocess import Popen, PIPE
from typing import BinaryIO

import numpy as np
from whisper import Whisper, load_model, transcribe

from core.data_access.logs import speech_to_text_log

model: Whisper = load_model("./data/whisperer.pt")
speech_to_text_log.info("Модель распознавания речи была загружена")

def convert_stream_to_data(stream: BinaryIO):
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

        results = np.frombuffer(stdout[44:], dtype=np.int16).astype(np.float32) / 32768.0
        flag = True

    except Exception as e:
        speech_to_text_log.error(f"Ошибка извлечения аудио: {e}")
        results = np.array([], dtype=np.float32)
        flag = False

    finally:
        if os.path.exists(temp_video_path):
            os.unlink(temp_video_path)

    return flag, results

async def get_text_from_audio_stream(stream: BinaryIO) -> str:
    success, result = convert_stream_to_data(stream)
    if not success:
        return ""

    result = transcribe(model=model, audio=result, language="ru")
    return result["text"]