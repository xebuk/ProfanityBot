from telegram import Update, Message
from telegram.ext import Application, MessageHandler, filters, ContextTypes, \
    CommandHandler, ChatMemberHandler

from time import time, sleep
from sched import scheduler
from atexit import register
from os import getenv
import logging

from textutil import analyse_message
from database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('./data/log.txt'),
        logging.StreamHandler()
    ]
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("Main Body")
BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не установлен! Проверьте .env файл")
    exit(1)

scheduler = scheduler(time, sleep)

warnings: set[str] = set()
database = DatabaseManager()

def on_timer(sc):
    with open("./data/words_with_warnings.txt", "a", encoding="utf8") as load_warnings:
        for word in warnings:
            load_warnings.write(f"{word}\n")
    warnings.clear()

    logger.info("Слова с предупреждениями были выгружены")
    sc.enter(600, 1, on_timer, (sc,))


def shutdown():
    with open("./data/words_with_warnings.txt", "a", encoding="utf8") as load_warnings:
        for word in warnings:
            load_warnings.write(f"{word}\n")

    logger.info("Данные успешно сохранены")


register(shutdown)


async def reply_to(text: str, letter: Message):
    user = letter.from_user
    text = text.lower()

    user_name = database.get_user_name(letter.chat_id, user.id)
    if user_name is None or user_name != user.name:
        database.add_or_update_name(letter.chat_id, user.id, user.name)

    if "сосал" in text:
        await letter.reply_text("сосал")
    if "я проиграл" in text:
        await letter.reply_text("я проиграл")

    curses, warned_words = analyse_message(user, text)
    warnings.update(warned_words)
    if curses != 0:
        database.add_to_curses(letter.chat_id, user.id, user.name, curses)
        await letter.reply_text(
            f"Ай-яй-яй, {user.name}, плохие слова говоришь... Целых {curses}!"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await reply_to(text, update.message)

async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.caption
    await reply_to(text, update.message)

async def handle_bot_join_or_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.my_chat_member
    new_status = chat_member.new_chat_member.status

    if new_status in {"member", "administrator"}:
        database.add_new_chat(update.message.chat_id)
        logger.info("Добавление чата в базу данных произведено успешно.")
    elif new_status in {"left", "kicked"}:
        database.deactivate_chat(update.message.chat_id)
        logger.info("Пометка чата как неактивного произведена успешно.")

async def handle_other_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_or_update_name(
        update.message.chat_id, update.message.from_user.id, update.message.from_user.name
    )
    logger.info("Добавление нового участника в таблицы чата произведено успешно.")

async def top_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Список из ада: \n"

    top = sorted(database.get_curses(update.message.chat_id), key=lambda x: (x[2], x[0]))
    index = 1
    summ = 0
    for i in range(len(top)):
        if top[i][2] == 0:
            continue
        message += f"{index}: {top[i][1]} - {top[i][2]}\n"
        summ += top[i][2]
        index += 1
    if message == "Список из ада: \n":
        await update.message.reply_text("Пока все ангелочки)")
    else:
        message += f"Итого: {summ}"
        await update.message.reply_text(message)

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )

    if chat_member.status in {"administrator", "owner"}:
        database.reset_chat(update.message.chat_id)
        logger.info("Сброс данных произведен успешно.")
    else:
        logger.info(f"У запрашивающего недостаточно прав - {update.message.from_user.name} - {update.chat_member.old_chat_member.status}")


def main():
    scheduler.enter(5, 1, on_timer, (scheduler,))

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("curse", top_curse_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.CAPTION, handle_message))
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_caption))

    app.add_handler(ChatMemberHandler(handle_bot_join_or_leave, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(handle_other_join, ChatMemberHandler.CHAT_MEMBER))

    logger.info("Бот запущен...")

    app.run_polling()


if __name__ == "__main__":
    main()
