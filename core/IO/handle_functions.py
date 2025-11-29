from io import BytesIO
from os import path, listdir
from queue import Queue
from random import choice, randint
from re import search

from telegram import Message, Update, VideoNote, Voice
from telegram.ext import ContextTypes

from core.analysis.messages import Messages
from core.analysis.speech_recognition import audio_queue
from core.analysis.textutil import split_and_clean, analyse_message
from core.data_access.config import NIGHTLY_BUILD_CHAT
from core.data_access.logs import functions_log
from core.data_access.database import access_point, DataType

def register_command(level: int, desc: str):
    def dec(func):
        setattr(func, "_handler_type", "command")
        setattr(func, "level", level)
        setattr(func, "desc", desc)
        return func
    return dec

def register_callback_handler(cond):
    def wrapper(func):
        setattr(func, "_handler_type", "callback_query")
        setattr(func, "cond", cond)
        return func
    return wrapper

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
            await update.message.reply_text(Messages.PRIVATE_MESSAGES)
            return None
        elif update.effective_chat.id not in chat_ids:
            if update.effective_chat.id not in chat_ids_on_queue:
                await update.message.reply_text(Messages.UNREGISTERED_CHAT)
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

media_send = {
    "webp" : lambda letter, file_path: letter.reply_sticker(file_path),
    "webm" : lambda letter, file_path: letter.reply_sticker(file_path),
    "mp4" : lambda letter, file_path: letter.reply_animation(file_path),
    "gif" : lambda letter, file_path: letter.reply_animation(file_path),
    "jpg" : lambda letter, file_path: letter.reply_photo(file_path),
}

media_queue: Queue[tuple[str, Message, str]] = Queue()

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
        if file.lower().endswith((".webp", ".webm", ".mp4", ".jpg", ".gif"))
    ]
    if not media_files:
        functions_log.info(f"В {meme_collection} нет подходящих файлов.")
        return

    random_file = choice(media_files)
    media_queue.put((
        random_file.split(".")[-1],
        letter,
        path.join(meme_collection, random_file)
    ))

async def reply_to(text: str, letter: Message):
    user = letter.from_user
    text = text.lower()

    privacy, trolling_status, regular_curse_update, curse_threshold = access_point.get_data_from_main_table(
        [DataType.PRIVACY, DataType.TROLLING_PERMIT, DataType.REGULAR_CURSE_UPDATE_PERMIT, DataType.CURSE_THRESHOLD],
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

    if search(r"с[ао]сал", text) is not None:
        await letter.reply_text("сосал")
    if search(r"я.+проиграл", text) is not None:
        await letter.reply_text("я проиграл")
    if search("/сурсе", text) is not None:
        await send_media(letter)
    if trolling_status == 1 and randint(1, 20) == 20:
        access_point.change_trolls(letter.chat_id, user.id, user.name)
        await letter.set_reaction(reaction="🤡")

    curses = analyse_message(user, split_and_clean(text), privacy == 1)
    if curses != 0:
        access_point.change_curses_userid(
            letter.chat_id,
            user.id,
            curses, user.name,
            delta=(regular_curse_update == 1)
        )
        if curses >= curse_threshold:
            await letter.reply_text(
                Messages.CURSE_REACTION.format(user.name, curses)
            )

async def handle_audio(audio: Voice | VideoNote, letter: Message):
    audio_stream = BytesIO()

    audio_file = await audio.get_file()
    await audio_file.download_to_memory(audio_stream)
    audio_queue.put((audio_stream, letter))

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
    await handle_audio(update.message.voice, update.message)

@check_if_message_exists("video_note")
@skip_filtered_updates
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_audio(update.message.video_note, update.message)

@check_if_message_exists("user")
@skip_filtered_updates
async def handle_other_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    access_point.add_or_update_name(
        update.effective_chat.id, update.effective_user.id, update.effective_user.name
    )