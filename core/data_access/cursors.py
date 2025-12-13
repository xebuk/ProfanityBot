from queue import SimpleQueue
from typing import BinaryIO, Final

from telegram import Message, File

from .logs import cursor_log

class Sentinel: ...

SHUTDOWN_SENTINEL: Final[Sentinel] = Sentinel()

audio_download_queue: SimpleQueue[tuple[File, Message]] = SimpleQueue()
audio_queue: SimpleQueue[tuple[BinaryIO, Message]] = SimpleQueue()
text_queue: SimpleQueue[tuple[str, Message]] = SimpleQueue()

media_queue: SimpleQueue[tuple[str, Message, str]] = SimpleQueue()

curses = open("./data/curses.txt", "a", encoding="utf8")
warnings = open("./data/warnings.txt", "a", encoding="utf8")
normal_words = open("./data/normal_words.txt", "a", encoding="utf8")

def graceful_exit():
    cursor_log.info("Активировано завершение работы")
    audio_download_queue.put(SHUTDOWN_SENTINEL)
    media_queue.put(SHUTDOWN_SENTINEL)
    curses.close()
    warnings.close()
    normal_words.close()
    cursor_log.info("Файлы слов закрыты")