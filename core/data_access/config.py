from os import getenv

from .logs import config_log

BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    config_log.error("BOT_TOKEN не установлен! Проверьте .env файл.")
    exit(1)

NIGHTLY_BUILD_CHAT = getenv("NIGHTLY_BUILD_CHAT")
if not NIGHTLY_BUILD_CHAT:
    config_log.warning("NIGHTLY_BUILD_CHAT не установлен! Проверьте .env файл.")
    NIGHTLY_BUILD_CHAT = 69
else:
    NIGHTLY_BUILD_CHAT = int(NIGHTLY_BUILD_CHAT)

DEBUG = True
SILENT = False