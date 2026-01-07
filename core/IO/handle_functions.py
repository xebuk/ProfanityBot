from datetime import datetime
from os import listdir
from os.path import exists
from random import choice, randint
from re import search, compile, fullmatch

from telegram import VideoNote, Voice, Message

from core.analysis import Messages, split_and_clean, analyse_message
from core.data_access import NIGHTLY_BUILD_CHAT, DEBUG, audio_download_queue, \
    media_queue, DataType, access_point, functions_log, server_tz

media_file_pattern = compile(r".+\.(web[pm]|jpe?g|gif|mp4)$")

async def send_media(letter: Message, category="all"):
    meme_collection = f"./media_nightly/{category}" if letter.chat_id == NIGHTLY_BUILD_CHAT else f"./media/{category}"
    if not exists(meme_collection):
        functions_log.info(f"Файл с мемами категории {category} не был найден - {meme_collection}")
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
        functions_log.info(f"Положил предмет категории {category} в очередь")

regex_replies = {
    compile(r"с[ао]сал") : lambda letter: letter.reply_text("сосал"),
    compile("я .*проиграл") : lambda letter: letter.reply_text("я проиграл"),
    compile("/сурсе") : send_media
}

async def act_on_letter(letter: Message):
    access_point.register_event(
        letter.chat_id,
        letter.from_user.id,
        "message", 1
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

    trolling_status, quiet_night_mode, sleep_start_time = access_point.get_data_from_main_table(
        [DataType.TROLLING_PERMIT, DataType.QUIET_NIGHT_MODE, DataType.SLEEP_START_TIME],
        [DataType.CHAT_ID],
        None,
        False, True,
        letter.chat_id
    )

    if trolling_status == 1 and randint(1, 20) == 20:
        access_point.register_event(
            letter.chat_id,
            letter.from_user.id,
            "troll", 1
        )
        await letter.set_reaction(reaction="🤡")
    if quiet_night_mode == 1:
        delta = letter.date.astimezone(server_tz) - datetime.strptime(
            sleep_start_time,
            "%Y-%m-%d %H:%M:%S.%f"
        ).astimezone(server_tz)

        if delta.total_seconds() // 3600 <= 10:
            access_point.register_event(
                letter.chat_id,
                letter.from_user.id,
                "insomnia", 1
            )
            if randint(1, 5) == 5:
                await send_media(letter, category="sleep")

async def act_on_text(text: str, letter: Message):
    privacy, curse_threshold = access_point.get_data_from_main_table(
        [DataType.PRIVACY, DataType.CURSE_THRESHOLD],
        [DataType.CHAT_ID],
        None,
        False, True,
        letter.chat_id
    )

    for pattern in regex_replies:
        if search(pattern, text.lower()) is not None:
            if DEBUG:
                functions_log.info(f"Активировался паттерн {pattern.pattern}")
            await regex_replies[pattern](letter)

    cleaned_text = split_and_clean(text.lower())
    access_point.register_event(
        letter.chat_id,
        letter.from_user.id,
        "word", len(cleaned_text)
    )

    curses = analyse_message(
        letter.from_user,
        cleaned_text,
        privacy == 1
    )
    if curses != 0:
        access_point.register_event(
            letter.chat_id,
            letter.from_user.id,
            "curse", curses
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