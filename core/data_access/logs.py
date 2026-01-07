import logging

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
logging.getLogger("apscheduler.scheduler").setLevel(logging.FATAL)
logging.getLogger("apscheduler.executors.default").setLevel(logging.FATAL)

config_log = logging.getLogger("Config")
logger_log = logging.getLogger("Logging")
database_log = logging.getLogger("Database")
cursor_log = logging.getLogger("Cursor")

main_body_log = logging.getLogger("Main Body")
prep_log = logging.getLogger("Preprocessing")
utils_log = logging.getLogger("Utils")
commands_log = logging.getLogger("Command")
functions_log = logging.getLogger("Function")
job_log = logging.getLogger("Job")
text_log = logging.getLogger("Text Management")
speech_to_text_log = logging.getLogger("STT")