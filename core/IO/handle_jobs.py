from queue import Empty
from io import BytesIO
from random import randint
from threading import Thread
from time import sleep

from telegram.ext import ContextTypes

from core.analysis import Messages, get_text_from_audio_stream
from core.data_access import DEBUG, SHUTDOWN_SENTINEL, audio_download_queue, \
    audio_queue, text_queue, media_queue, DataType, access_point, job_log

from .handle_functions import reply_to
from .handler_utils import register_job, job_queue, register_job_repeating

@register_job(randint(3600, 21600))
async def random_send(context: ContextTypes.DEFAULT_TYPE):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID, DataType.RANDOM_SEND_MESSAGE],
        [DataType.RANDOM_SEND_PERMIT],
        None,
        False, False,
        1
    )
    for chat_id, message in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, disable_notification=True)
            job_log.info(Messages.RANDOM_SEND_LOGGING_SUCCESS.format(chat_id))
        except Exception as e:
            job_log.info(Messages.RANDOM_SEND_LOGGING_FAILURE.format(chat_id, e))

    job_queue.run_once(random_send, randint(3600, 21600))

@register_job_repeating(7200)
async def regular_top(context: ContextTypes.DEFAULT_TYPE):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        [DataType.REGULAR_CURSE_UPDATE_PERMIT],
        None,
        False, False,
        1
    )
    for chat_id in chat_ids:
        await context.bot.send_message(chat_id=chat_id[0], text=Messages.REGULAR_TOP, disable_notification=True)
        top = sorted(
            access_point.get_data_from_chat(
                chat_id[0],
                [DataType.USER_ID, DataType.USER_NAME, DataType.CURSES_DELTA],
                None,
                [DataType.CURSES_DELTA], True,
                False
            ),
            key=lambda x: (x[2], x[0])
        )
        if top[-1][2] == 0:
            await context.bot.send_message(chat_id=chat_id[0], text=Messages.REGULAR_TOP_ALL_POLITE, disable_notification=True)
            continue

        await context.bot.send_message(chat_id=chat_id[0], text=Messages.REGULAR_TOP_ALL_TRAGEDY, disable_notification=True)
        message = Messages.TOP_CURSE_REFRESH

        index = 1
        summ = 0
        for i in range(len(top)):
            if top[i][2] == 0:
                continue
            message += Messages.TOP_ENTRY.format(index, top[i][1], top[i][2])
            summ += top[i][2]
            index += 1

            access_point.change_curses_userid(chat_id[0], top[i][0], top[i][2], None)
        message += Messages.TOP_RESULT.format(summ)
        await context.bot.send_message(chat_id=chat_id[0], text=message, disable_notification=True)
        access_point.reset_curses_delta(chat_id[0])

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

        await reply_to(*entry)
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