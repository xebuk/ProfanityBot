from telegram import Update, Message
from telegram.ext import Application, MessageHandler, filters, ContextTypes, \
    CommandHandler, ChatMemberHandler, JobQueue

from re import search
from random import randint, choice
from atexit import register
from os import getenv, path, listdir
from io import BytesIO

from database import DatabaseManager, DataType
from logs import main_body_log
from speech_recognition import get_text_from_stream
from textutil import analyse_message, split_and_clean

BOT_TOKEN = getenv("BOT_TOKEN")
if not BOT_TOKEN:
    main_body_log.error("BOT_TOKEN не установлен! Проверьте .env файл")
    exit(1)

DEBUG = getenv("DEBUG")
if not BOT_TOKEN:
    DEBUG = False
else:
    DEBUG = (DEBUG == "true")

database = DatabaseManager()

register(database.shutdown)

def get_media():
    if not path.exists("./media"):
        main_body_log.info("Папка media не найдена!")
        return "", ""

    media_files = [
        file for file in listdir("./media")
        if file.lower().endswith((".webp", ".mp4"))
    ]
    if not media_files:
        main_body_log.info("В папке media нет нужных файлов!")
        return "", ""

    random_file = choice(media_files)
    file_path = path.join("./media", random_file)

    return file_path, file_path.split(".")[-1]

async def reply_to(text: str, letter: Message):
    user = letter.from_user
    text = text.lower()

    privacy = database.get_data_from_main_table(
        [DataType.PRIVACY],
        [DataType.CHAT_ID],
        None,
        False, True,
        letter.chat_id
    )[0] == 1
    user_name = database.get_data_from_chat(
        letter.chat_id,
        [DataType.USER_NAME],
        [DataType.USER_ID],
        None,
        False, True,
        user.id
    )
    if user_name is None or user_name != user.name:
        database.add_or_update_name(letter.chat_id, user.id, user.name)

    if search("сосал", text) is not None:
        await letter.reply_text("сосал")
    if search(" я ", text) is not None and search("проиграл", text) is not None:
        await letter.reply_text("я проиграл")
    if search("/сурсе", text) is not None:
        main_body_log.info("Обнаружил /сурсе")
        file_path, file_ext = get_media()
        main_body_log.info(f"Получил путь - {file_path} - {file_ext}")
        if file_path != "":
            with open(file_path, 'rb') as file:
                match file_ext:
                    case "webp": await letter.reply_sticker(file)
                    case "mp4": await letter.reply_animation(file)

    curses = analyse_message(user, split_and_clean(text), privacy)
    if curses != 0:
        database.change_curses_userid(letter.chat_id, user.id, curses, user.name)
        await letter.reply_text(
            f"Ай-яй-яй, {user.name}, плохие слова говоришь... Целых {curses}!"
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        text = update.message.text
        await reply_to(text, update.message)

async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        text = update.message.caption
        await reply_to(text, update.message)

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None and update.message.voice is not None:
        voice_stream = BytesIO()

        voice_file = await update.message.voice.get_file()
        await voice_file.download_to_memory(voice_stream)

        text = get_text_from_stream(voice_stream)

        voice_stream.flush()
        voice_stream.close()

        await reply_to(text, update.message)

async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None and update.message.video_note is not None:
        video_note_stream = BytesIO()

        video_note_file = await update.message.video_note.get_file()
        await video_note_file.download_to_memory(video_note_stream)

        text = get_text_from_stream(video_note_stream)

        video_note_stream.flush()
        video_note_stream.close()

        await reply_to(text, update.message)

async def handle_bot_join_or_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.my_chat_member
    new_status = chat_member.new_chat_member.status

    if new_status in {"member", "administrator"}:
        database.add_new_chat(update.message.chat_id)
        database.update_data_from_main_table(
            [DataType.CHAT_NAME],
            [DataType.CHAT_ID],
            update.message.chat.effective_name, update.message.chat_id
        )
        main_body_log.info(f"Добавление чата {update.message.chat_id} в базу данных произведено успешно.")
    elif new_status in {"left", "kicked"}:
        database.deactivate_chat(update.message.chat_id)
        main_body_log.info(f"Пометка чата {update.message.chat_id} как неактивного произведена успешно.")

async def handle_other_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    database.add_or_update_name(
        update.message.chat_id, update.message.from_user.id, update.message.from_user.name
    )

async def top_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Список из ада: \n"
    top = sorted(
        database.get_data_from_chat(
            update.message.chat_id,
            [DataType.USER_ID, DataType.USER_NAME, DataType.CURSES],
            None,
            [DataType.CURSES],
            True, False
        ),
        key=lambda x: (x[2], x[0])
    )

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

async def change_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    if context.args[0] and context.args[1]:
        callback = database.change_curses_username(
            update.message.chat_id,
            context.args[0],
            int(context.args[1])
        )
        if callback:
            await update.message.reply_text("Рейтинг изменен успешно.")
        else:
            await update.message.reply_text("Не удалось изменить рейтинг. Попробуйте позже.")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )

    if chat_member.status in {"administrator", "owner"}:
        database.reset_chat(update.message.chat_id)
        await update.message.reply_text("Сброс данных произведен успешно.")
    else:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")

async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "ВНИМАНИЕ!\n"

    all_user_names = sorted(
        database.get_data_from_chat(
            update.message.chat_id,
            [DataType.USER_NAME],
            None,
            None,
            False,False
        ),
        key=lambda x: x[0].lower()
    )
    for i in all_user_names:
        message += f"{i[0]}\n"
    message += "Спасибо за внимание."
    await update.message.reply_text(message)

async def set_donation_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    if not context.args:
        await update.message.reply_text("Вы не ввели ссылку для доната!")
        return

    database.update_data_from_main_table(
        [DataType.DONATION_LINK],
        [DataType.CHAT_ID],
        " ".join(context.args), update.message.chat_id
    )

async def donation_link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    donation_link = database.get_data_from_main_table(
        [DataType.DONATION_LINK],
        [DataType.CHAT_ID],
        None,False, True,
        update.message.chat_id
    )
    await update.message.reply_text(donation_link)

async def permit_to_random_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    changed, permit = database.change_random_send_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(f"Статус случайной отправки в данный чат изменен на {result}")
    else:
        await update.message.reply_text(f"Статус случайной отправки в данный чат не был изменен. Попробуйте ещё раз.")

async def set_random_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    if not context.args:
        await update.message.reply_text("Вы не ввели сообщение для случайной отправки!")
        return

    database.update_data_from_main_table(
        [DataType.RANDOM_SEND_MESSAGE],
        [DataType.CHAT_ID],
        " ".join(context.args), update.message.chat_id
    )

async def random_send(context: ContextTypes.DEFAULT_TYPE):
    chat_ids = database.get_data_from_main_table(
        [DataType.CHAT_ID, DataType.RANDOM_SEND_MESSAGE],
        [DataType.IS_PERMITTED_TO_RANDOM_SEND],
        None,
        False, False,
        1
    )
    for chat_id, message in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, disable_notification=True)
            main_body_log.info(f"Случайное сообщение было отправлено в {chat_id}")
        except Exception as e:
            main_body_log.info(f"Случайное сообщение не было отправлено в {chat_id}: {e}")

    app.job_queue.run_once(random_send, randint(3600, 21600))

job_queue = JobQueue()

async def on_start(appl: Application):
    job_queue.set_application(appl)
    await job_queue.start()
    job_queue.run_once(random_send, randint(3600, 14400))

app = (Application.builder()
       .token(BOT_TOKEN)
       .read_timeout(30)
       .write_timeout(30)
       .connect_timeout(30)
       .pool_timeout(30)
       .post_init(on_start)
       .build())

def main():
    app.add_handler(CommandHandler("curse", top_curse_command))
    app.add_handler(CommandHandler("change_curse", change_curse_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("all", all_command))
    app.add_handler(CommandHandler("set_donate", set_donation_link))
    app.add_handler(CommandHandler("donate", donation_link_command))
    app.add_handler(CommandHandler("random_send", permit_to_random_send_command))
    app.add_handler(CommandHandler("set_random_send_message", set_random_send_message))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.CAPTION, handle_message))
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_caption)),
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))

    app.add_handler(ChatMemberHandler(handle_bot_join_or_leave, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(handle_other_join, ChatMemberHandler.CHAT_MEMBER))

    app.run_polling()

if __name__ == "__main__":
    main()
