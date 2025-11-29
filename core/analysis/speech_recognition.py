import queue

from atexit import register
from os import path, unlink
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from threading import Thread
from typing import BinaryIO

import numpy as np
from telegram import Message, File
from whisper import Whisper, load_model, transcribe

from core.data_access.config import SHUTDOWN_SENTINEL
from core.data_access.logs import speech_to_text_log

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

        result = np.frombuffer(stdout[44:], dtype=np.int16).astype(np.float32) / 32768.0
        success = True
    except Exception as e:
        speech_to_text_log.error(f"Ошибка извлечения аудио: {e}")
        result = np.array([], dtype=np.float32)
        success = False
    finally:
        if path.exists(temp_video_path):
            unlink(temp_video_path)

    if not success:
        return ""

    result = transcribe(model=model, audio=result, language="ru")
    return result["text"]

audio_queue: queue.Queue[tuple[BinaryIO, Message]] = queue.Queue()
text_queue: queue.Queue[tuple[str, Message]] = queue.Queue()

def speech_to_text_processing():
    while True:
        try:
            entry = audio_queue.get()
            if entry is SHUTDOWN_SENTINEL:
                audio_queue.shutdown()
                text_queue.put(SHUTDOWN_SENTINEL)
                break

            audio_stream, letter = entry
            text = get_text_from_audio_stream(audio_stream)
            audio_stream.flush()
            audio_stream.close()

            text_queue.put((text, letter))
            audio_queue.task_done()
        except queue.ShutDown:
            speech_to_text_log.error("Очередь закрыта")
            break
        except Exception as e:
            speech_to_text_log.error(f"Ошибка обработки аудио: {e}")
            text_queue.put(("", letter))

speech_to_text_thread = Thread(None, speech_to_text_processing, daemon=True)
speech_to_text_thread.start()

@register
def shutdown():
    speech_to_text_log.info("Запустил функцию выхода")
    audio_queue.put(SHUTDOWN_SENTINEL)
    speech_to_text_thread.join()