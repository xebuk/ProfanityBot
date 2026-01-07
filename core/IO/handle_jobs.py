from datetime import datetime
from queue import Empty
from io import BytesIO
from random import randint
from threading import Thread
from time import sleep

from telegram.ext import ContextTypes

from core.analysis import Messages, get_text_from_audio_stream
from core.data_access import DEBUG, SHUTDOWN_SENTINEL, audio_download_queue, \
    audio_queue, text_queue, media_queue, DataType, access_point, job_log

from .handle_functions import act_on_text
from .handler_utils import register_job, job_queue, register_job_repeating, \
    transform_event_data, two_hours_ago

@register_job(randint(3600, 21600))
async def random_send(context: ContextTypes.DEFAULT_TYPE):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID, DataType.RANDOM_SEND_MESSAGE],
        [DataType.RANDOM_SEND_PERMIT, DataType.IS_ACTIVE],
        None,
        False, False,
        1, 1
    )
    for chat_id, message in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, disable_notification=True)
            job_log.info(Messages.RANDOM_SEND_LOGGING_SUCCESS.format(chat_id))
        except Exception as e:
            job_log.info(Messages.RANDOM_SEND_LOGGING_FAILURE.format(chat_id, e))

    job_queue.run_once(random_send, randint(3600, 21600))

async def construct_and_send_regular_top(context: ContextTypes.DEFAULT_TYPE, chat_id: int, top_type: str):
    (start_message, nothing_message, something_message,
     event_group, amount_command, in_reverse,
     map_lambda, sort_lambda) = regular_top_arguments[top_type]

    top = list(map(map_lambda, sorted(transform_event_data(
        event_group,
        access_point.pull_chat_wide_event(chat_id, amount_command, two_hours_ago)
    ), key=sort_lambda, reverse=in_reverse)))

    if not top:
        await context.bot.send_message(chat_id=chat_id, text=nothing_message, disable_notification=True)
        return

    message = start_message

    index = 0
    summ = 0
    previous_score = None

    for i in range(len(top)):
        if top[i][1] == 0:
            continue
        if top[i][1] != previous_score:
            previous_score = top[i][1]
            index += 1
        message += Messages.TOP_ENTRY.format(
            index, top[i][0], round(top[i][1], 2)
        )
        summ += top[i][1]

    message = something_message + message
    message += Messages.TOP_RESULT.format(summ)
    await context.bot.send_message(chat_id=chat_id, text=message, disable_notification=True)

regular_top_arguments = {
    "curse" : (
        Messages.TOP_CURSE_REFRESH,
        Messages.TOP_CURSE_REFRESH_EVERYONE_IS_POLITE,
        Messages.TOP_CURSE_REFRESH_TRAGEDY,
        ("curse",),
        "sum",
        False,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    ),
    "troll": (
        Messages.TOP_TROLLING_REFRESH,
        Messages.TOP_TROLLING_REFRESH_NO_CLOWN,
        Messages.TOP_TROLLING_REFRESH_TRAGEDY,
        ("troll",),
        "sum",
        False,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    ),
    "shot_at": (
        Messages.TOP_SHOT_REFRESH,
        Messages.TOP_SHOT_REFRESH_CLEAR_GAUZE,
        Messages.TOP_SHOT_REFRESH_TRAGEDY,
        ("shot_at",),
        "sum",
        False,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    )
}

regular_top_order = ["curse", "troll", "shot_at"]

@register_job_repeating(7200)
async def regular_top(context: ContextTypes.DEFAULT_TYPE):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        [DataType.REGULAR_UPDATE_PERMIT, DataType.IS_ACTIVE],
        None,
        False, False,
        1, 1
    )
    for chat_id in chat_ids:
        await context.bot.send_message(chat_id=chat_id[0], text=Messages.REGULAR_TOP, disable_notification=True)
        for top_type in regular_top_order:
            await construct_and_send_regular_top(context, chat_id[0], top_type)

@register_job_repeating(3600)
async def one_hour(context: ContextTypes.DEFAULT_TYPE):
    chats_and_their_timers = access_point.get_data_from_main_table(
        [DataType.CHAT_ID, DataType.SLEEP_START_TIME],
        [DataType.IS_ACTIVE, DataType.QUIET_NIGHT_MODE],
        None,
        False, False,
        1, 1
    )

    for chat_id, sleep_start_time in chats_and_their_timers:
        if sleep_start_time == "stub":
            continue

        delta = datetime.now() - datetime.strptime(sleep_start_time, "%Y-%m-%d %H:%M:%S.%f")
        if delta.total_seconds() // 3600 < 10:
            continue

        access_point.update_data_from_main_table(
            [DataType.QUIET_NIGHT_MODE],
            [DataType.CHAT_ID],
            0, chat_id
        )

        all_user_names = sorted(
            access_point.get_data_from_chat(
                chat_id,
                [DataType.USER_NAME],
                None,
                None, False,
                False
            ),
            key=lambda x: x[0].lower()
        )

        message = ""
        for i in all_user_names:
            message += f"{i[0]}\n"
        message += Messages.GOOD_AWAKENING
        await context.bot.send_message(chat_id=chat_id, text=message)

    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        [DataType.HIGH_NOON_SHOWDOWN_PERMIT, DataType.IS_ACTIVE],
        None,
        False, False,
        1, 1
    )

    for chat_id in chat_ids:
        access_point.update_data_from_chat(
            chat_id[0],
            [DataType.BULLET_POSSESSION],
            None,
            6
        )

@register_job_repeating(5)
async def handle_audio_download_callback(context: ContextTypes.DEFAULT_TYPE):
    try:
        entry = audio_download_queue.get(timeout=0.2)
        if entry is SHUTDOWN_SENTINEL:
            job_log.info("Очередь файлов аудио на подгрузку закрыта")
            audio_queue.put(SHUTDOWN_SENTINEL)
            return

        audio_stream = BytesIO()
        audio_file, letter = entry

        await audio_file.download_to_memory(audio_stream)
        audio_queue.put((audio_stream, letter))
    except Empty:
        pass
    except Exception as e:
        job_log.error(f"Возникла непредвиденная ошибка - {e}")

@register_job_repeating(5)
async def handle_audio_callback(context: ContextTypes.DEFAULT_TYPE):
    try:
        entry = text_queue.get(timeout=0.2)
        if entry is SHUTDOWN_SENTINEL:
            job_log.info("Очередь текста на анализ закрыта")
            return

        await act_on_text(*entry)
    except Empty:
        pass
    except Exception as e:
        job_log.error(f"Возникла непредвиденная ошибка - {e}")

media_send = {
    "webp" : lambda letter, file_path: letter.reply_sticker(file_path),
    "webm" : lambda letter, file_path: letter.reply_sticker(file_path),
    "mp4" : lambda letter, file_path: letter.reply_animation(file_path),
    "gif" : lambda letter, file_path: letter.reply_animation(file_path),
    "jpg" : lambda letter, file_path: letter.reply_photo(file_path),
}

@register_job_repeating(1)
async def handle_media_callback(context: ContextTypes.DEFAULT_TYPE):
    try:
        entry = media_queue.get(timeout=0.2)
        if entry is SHUTDOWN_SENTINEL:
            job_log.info("Очередь изображений на отправку закрыта")
            return
        file_ext, letter, file_path = entry

        if DEBUG:
            job_log.info(f"Получил файл - {file_path}")

        await media_send[file_ext](letter, file_path)
    except Empty:
        pass
    except Exception as e:
        job_log.error(f"Возникла непредвиденная ошибка - {e}")

def speech_to_text_processing():
    while True:
        try:
            entry = audio_queue.get(timeout=0.2)
            if entry is SHUTDOWN_SENTINEL:
                job_log.info("Очередь аудио на конвертирование в текст закрыта")
                text_queue.put(SHUTDOWN_SENTINEL)
                break

            audio_stream, letter = entry
            text = get_text_from_audio_stream(audio_stream)
            audio_stream.flush()
            audio_stream.close()

            if text == "":
                continue

            text_queue.put((text, letter))
        except Empty:
            pass
        except Exception as e:
            job_log.error(f"Ошибка обработки аудио: {e}")

        sleep(5)

speech_to_text_thread = Thread(None, speech_to_text_processing)
speech_to_text_thread.start()