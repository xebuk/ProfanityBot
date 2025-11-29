import sys
import signal
from queue import Empty

from telegram import BotCommandScopeAllChatAdministrators, \
    BotCommandScopeAllGroupChats, BotCommand
from telegram.ext import Application, ContextTypes, JobQueue, CommandHandler, \
    MessageHandler, ChatMemberHandler, CallbackQueryHandler, filters

from random import randint

import core.IO.handle_commands

from core.IO.handle_functions import reply_to, handle_other_join, \
    handle_video_note, handle_voice_message, handle_caption, handle_message, \
    media_queue, media_send
from core.analysis.messages import Messages
from core.analysis.speech_recognition import text_queue
from core.data_access.config import BOT_TOKEN, SHUTDOWN_SENTINEL
from core.data_access.database import access_point, DataType
from core.data_access.logs import main_body_log

group_chat_commands = list()
group_admins_commands = list()
handlers_list = list()

for name in vars(core.IO.handle_commands):
    func = getattr(core.IO.handle_commands, name)
    if hasattr(func, "_handler_type"):
        match getattr(func, "_handler_type"):
            case "command":
                command = name.replace('_command', '')
                handlers_list.append(CommandHandler(command, func))
                if func.level < 2: group_chat_commands.append(BotCommand(command, func.desc))
                if func.level < 3: group_admins_commands.append(BotCommand(command, func.desc))
            case "message": handlers_list.append(MessageHandler(func.fil, func))
            case "chat_member": handlers_list.append(ChatMemberHandler(func, func.chat_member))
            case "callback_query": handlers_list.append(CallbackQueryHandler(func, func.cond))

def graceful_exit(signum, frame):
    main_body_log.info("Активировано завершение работы")
    sys.exit(0)

signal.signal(signal.SIGTERM, graceful_exit)
signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGQUIT, graceful_exit)

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
            main_body_log.info(Messages.RANDOM_SEND_LOGGING_SUCCESS.format(chat_id))
        except Exception as e:
            main_body_log.info(Messages.RANDOM_SEND_LOGGING_FAILURE.format(chat_id, e))

    app.job_queue.run_once(random_send, randint(3600, 21600))

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

async def handle_audio_callback(context: ContextTypes.DEFAULT_TYPE):
    try:
        entry = text_queue.get(timeout=0.1)
        if entry is SHUTDOWN_SENTINEL:
            text_queue.shutdown()
            return
        await reply_to(*entry)
    except Exception:
        pass

    job_queue.run_once(handle_audio_callback, 5)

async def handle_media_callback(context: ContextTypes.DEFAULT_TYPE):
    entry = None
    try:
        entry = media_queue.get(timeout=0.1)
        if entry is SHUTDOWN_SENTINEL:
            media_queue.shutdown()
            return
        file_ext, letter, file_path = entry

        sent_message = await media_send[file_ext](letter, file_path)
        if sent_message is None: raise Exception("Сообщение не было отправлено")
    except Empty:
        pass
    except Exception:
        if entry is not None:
            media_queue.put(entry)

    job_queue.run_once(handle_media_callback, 1)

job_queue = JobQueue()

async def on_start(appl: Application):
    job_queue.set_application(appl)
    await job_queue.start()
    job_queue.run_once(random_send, randint(3600, 14400))
    job_queue.run_repeating(regular_top, 7200)
    job_queue.run_once(handle_audio_callback, 5)
    job_queue.run_once(handle_media_callback, 1)

    await appl.bot.set_my_commands(
        group_chat_commands,
        scope=BotCommandScopeAllGroupChats()
    )
    await appl.bot.set_my_commands(
        group_admins_commands,
        scope=BotCommandScopeAllChatAdministrators()
    )

    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        None,
        None,
        False, False
    )
    for chat_id in chat_ids:
        await appl.bot.send_message(chat_id=chat_id[0], text=Messages.I_AWAKE, disable_notification=True)

async def on_stop(appl: Application):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        None,
        None,
        False, False
    )
    for chat_id in chat_ids:
        await appl.bot.send_message(chat_id=chat_id[0], text=Messages.I_SLEEP, disable_notification=True)

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(on_start)
    .post_stop(on_stop)
    .build()
)

if __name__ == "__main__":
    for handler in handlers_list:
        app.add_handler(handler)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.CAPTION, handle_message))
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_caption))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))

    app.add_handler(ChatMemberHandler(handle_other_join, ChatMemberHandler.CHAT_MEMBER))

    app.run_polling()