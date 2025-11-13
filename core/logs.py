import logging
from atexit import register

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler("./data/log.txt"),
        logging.StreamHandler(),
    ]
)

logging.getLogger("httpx").setLevel(logging.FATAL)
logging.getLogger("httpcore").setLevel(logging.FATAL)

main_body_log = logging.getLogger("Main Body")
text_log = logging.getLogger("Text Management")
database_log = logging.getLogger("Database")
speech_to_text_log = logging.getLogger("STT")

curses = open("./data/curses.txt", "a", encoding="utf8")
warnings = open("./data/warnings.txt", "a", encoding="utf8")
normal_words = open("./data/normal_words.txt", "a", encoding="utf8")

@register
def shutdown_file_logging():
    curses.close()
    warnings.close()
    normal_words.close()
