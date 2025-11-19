import random
from io import BytesIO
from os import path, listdir
from random import choice
from re import search

from telegram import Message, Update
from telegram.error import RetryAfter, TelegramError
from telegram.ext import ContextTypes

from core.analysis.speech_recognition import get_text_from_audio_stream
from core.analysis.textutil import split_and_clean, analyse_message
from core.data_access.config import NIGHTLY_BUILD_CHAT
from core.data_access.logs import functions_log
from core.data_access.database import access_point, DataType

def skip_filtered_updates(handler):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_ids = set(
            int(i[0]) for i in access_point.get_data_from_main_table(
                [DataType.CHAT_ID],
                None,
                None,
                False, False
            )
        )
        chat_ids_on_queue = set(
            int(i[0]) for i in access_point.get_data_from_queue(
                [DataType.CHAT_ID],
                False
            )
        )

        if update.effective_chat.type == "private":
            await update.message.reply_text("Данный бот не работает в личных сообщениях.")
            return None
        elif update.effective_chat.id not in chat_ids:
            if update.effective_chat.id not in chat_ids_on_queue:
                await update.message.reply_text("Данный чат не находится в зарегистрированных. Тыкните владельца бота для дальнейших действий.")
            access_point.insert_data_into_queue(update.effective_chat.id, update.effective_chat.effective_name)
            return None

        return await handler(update, context)
    return wrapper

message_existence = {
    "user": lambda update: update.effective_user is None,
    "text": lambda update: update.message.text is None,
    "caption": lambda update: update.message.caption is None,
    "voice": lambda update: update.message.voice is None,
    "video_note": lambda update: update.message.video_note is None,
    "photo": lambda update: update.message.photo is None
}

def check_if_message_exists(argument: str):
    def check(handler):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.message is None or message_existence[argument](update):
                return None
            return await handler(update, context)
        return wrapper
    return check

async def send_media(letter: Message):
    if letter.chat_id == NIGHTLY_BUILD_CHAT:
        meme_collection = "./media_nightly"
    else:
        meme_collection = "./media"
    if not path.exists(meme_collection):
        functions_log.info(f"Файл с мемами не был найден - {meme_collection}")
        return

    media_files = [
        file for file in listdir(meme_collection)
        if file.lower().endswith((".webp", ".mp4", ".jpg", ".gif"))
    ]
    if not media_files:
        functions_log.info(f"В {meme_collection} нет подходящих файлов.")
        return

    random_file = choice(media_files)
    file_path = path.join(meme_collection, random_file)
    file_ext = random_file.split(".")[-1]

    if file_path != "":
        functions_log.info(f"Выбран файл - {random_file}")
        with open(file_path, 'rb') as file:
            for attempt in range(1, 6):
                try:
                    match file_ext:
                        case "webp": await letter.reply_sticker(file)
                        case "mp4", "gif": await letter.reply_animation(file)
                        case "jpg": await letter.reply_photo(file)
                except RetryAfter as e:
                    if letter.chat_id == NIGHTLY_BUILD_CHAT:
                        functions_log.error(f"Попытка {attempt} - поймал RetryAfter - {e}")
                    continue
                except TelegramError as e:
                    if letter.chat_id == NIGHTLY_BUILD_CHAT:
                        functions_log.error(f"Попытка {attempt} - поймал TelegramError - {e}")
                    continue
                break

async def reply_to(text: str, letter: Message):
    user = letter.from_user
    text = text.lower()

    privacy, trolling_status = access_point.get_data_from_main_table(
        [DataType.PRIVACY, DataType.CAN_BE_TROLLED],
        [DataType.CHAT_ID],
        None,
        False, True,
        letter.chat_id
    )
    user_name = access_point.get_data_from_chat(
        letter.chat_id,
        [DataType.USER_NAME],
        [DataType.USER_ID],
        None,
        False, True,
        user.id
    )
    if user_name is None or user_name != user.name:
        access_point.add_or_update_name(letter.chat_id, user.id, user.name)

    if search("сосал", text) is not None:
        await letter.reply_text("сосал")
    if search(" я ", text) is not None and search("проиграл", text) is not None:
        await letter.reply_text("я проиграл")
    if search("/сурсе", text) is not None:
        await send_media(letter)
    if trolling_status == 1 and random.randint(1, 20) == 20:
        access_point.change_trolls(letter.chat_id, user.id, user.name)
        await letter.set_reaction(reaction="🤡")

    curses = analyse_message(user, split_and_clean(text), privacy == 1)
    if curses != 0:
        access_point.change_curses_userid(letter.chat_id, user.id, curses, user.name)
        if curses > 1:
            await letter.reply_text(
                f"Ай-яй-яй, {user.name}, плохие слова говоришь... Целых {curses}!"
            )

@check_if_message_exists("text")
@skip_filtered_updates
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_to(update.message.text, update.message)

@check_if_message_exists("caption")
@skip_filtered_updates
async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_to(update.message.caption, update.message)

@check_if_message_exists("voice")
@skip_filtered_updates
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice_stream = BytesIO()

    voice_file = await update.message.voice.get_file()
    await voice_file.download_to_memory(voice_stream)

    text = await get_text_from_audio_stream(voice_stream)

    voice_stream.flush()
    voice_stream.close()

    await reply_to(text, update.message)

@check_if_message_exists("video_note")
@skip_filtered_updates
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video_note_stream = BytesIO()

    video_note_file = await update.message.video_note.get_file()
    await video_note_file.download_to_memory(video_note_stream)

    text = await get_text_from_audio_stream(video_note_stream)

    video_note_stream.flush()
    video_note_stream.close()

    await reply_to(text, update.message)

@check_if_message_exists("user")
@skip_filtered_updates
async def handle_other_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    access_point.add_or_update_name(
        update.effective_chat.id, update.effective_user.id, update.effective_user.name
    )