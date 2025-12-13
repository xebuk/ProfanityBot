from os import listdir
from os.path import exists
from random import choice, randint
from re import search, compile, fullmatch

from telegram import Update, VideoNote, Voice, Message
from telegram.ext import ContextTypes, filters

from core.analysis import Messages, split_and_clean, analyse_message
from core.data_access import NIGHTLY_BUILD_CHAT, DEBUG, audio_download_queue, \
    media_queue, DataType, access_point, functions_log

from .handler_utils import register_message_handler, check_if_message_exists, \
    skip_filtered_updates, register_chat_member_handler

media_file_pattern = compile(r".+\.(web[pm]|jpe?g|gif|mp4)$")

async def send_media(letter: Message):
    meme_collection = "./media_nightly" if letter.chat_id == NIGHTLY_BUILD_CHAT else "./media"
    if not exists(meme_collection):
        functions_log.info(f"Файл с мемами не был найден - {meme_collection}")
        return

    media_files = list()
    for file in listdir(meme_collection):
        file_match = fullmatch(media_file_pattern, file)
        if file_match is None:
            continue
        media_files.append((file_match.group(0), file_match.group(1)))

    if not media_files:
        functions_log.info(f"В {meme_collection} нет подходящих файлов.")
        return

    random_file = choice(media_files)
    if DEBUG:
        functions_log.info(f"Выбрал файл - {random_file}")

    media_queue.put((
        random_file[1],
        letter,
        f"{meme_collection}/{random_file[0]}"
    ))
    if DEBUG:
        functions_log.info("Положил предмет в очередь")

regex_replies = {
    compile(r"с[ао]сал") : lambda letter: letter.reply_text("сосал"),
    compile("я .*проиграл") : lambda letter: letter.reply_text("я проиграл"),
    compile("/сурсе") : send_media
}

async def reply_to(text: str, letter: Message):
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
        letter.from_user.id
    )

    if user_name is None or user_name != letter.from_user.name:
        access_point.add_or_update_name(
            letter.chat_id,
            letter.from_user.id,
            letter.from_user.name
        )

    for pattern in regex_replies:
        if search(pattern, text.lower()) is not None:
            if DEBUG:
                functions_log.info(f"Активировался паттерн {pattern.pattern}")
            await regex_replies[pattern](letter)
    if trolling_status == 1 and randint(1, 20) == 20:
        access_point.change_trolls(
            letter.chat_id,
            letter.from_user.id,
            letter.from_user.name
        )
        await letter.set_reaction(reaction="🤡")

    curses = analyse_message(
        letter.from_user,
        split_and_clean(text.lower()),
        privacy == 1
    )
    if curses != 0:
        access_point.change_curses_userid(
            letter.chat_id,
            letter.from_user.id,
            curses, letter.from_user.name,
            delta=(regular_curse_update == 1)
        )
        if curses >= curse_threshold:
            await letter.reply_text(
                Messages.CURSE_REACTION.format(
                    letter.from_user.name,
                    curses
                )
            )

async def handle_audio(audio: Voice | VideoNote, letter: Message):
    audio_file = await audio.get_file()
    audio_download_queue.put((audio_file, letter))

@register_message_handler(filters.TEXT & ~filters.CAPTION)
@check_if_message_exists("text")
@skip_filtered_updates
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_to(update.effective_message.text, update.effective_message)

@register_message_handler(filters.CAPTION)
@check_if_message_exists("caption")
@skip_filtered_updates
async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await reply_to(update.effective_message.caption, update.effective_message)

@register_message_handler(filters.VOICE)
@check_if_message_exists("voice")
@skip_filtered_updates
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_audio(update.effective_message.voice, update.effective_message)

@register_message_handler(filters.VIDEO_NOTE)
@check_if_message_exists("video_note")
@skip_filtered_updates
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_audio(update.effective_message.video_note, update.effective_message)

@register_chat_member_handler(0)
@check_if_message_exists("user")
@skip_filtered_updates
async def handle_other_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    access_point.add_or_update_name(
        update.effective_chat.id, update.effective_user.id, update.effective_user.name
    )