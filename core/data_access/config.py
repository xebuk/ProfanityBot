from os import getenv

from core.data_access.logs import config_log

BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    config_log.error("BOT_TOKEN не установлен! Проверьте .env файл.")
    exit(1)

DEBUG = getenv("DEBUG")
if not DEBUG:
    DEBUG = False
else:
    DEBUG = (DEBUG == "true")

NIGHTLY_BUILD_CHAT = getenv("NIGHTLY_BUILD_CHAT")
if not NIGHTLY_BUILD_CHAT:
    NIGHTLY_BUILD_CHAT = 69
else:
    NIGHTLY_BUILD_CHAT = int(NIGHTLY_BUILD_CHAT)