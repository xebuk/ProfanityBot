from functools import wraps

from telegram import Update, BotCommand
from telegram.ext import MessageHandler, ChatMemberHandler, ContextTypes, \
    CallbackQueryHandler, JobQueue, Application, CommandHandler

from core.analysis import Messages
from core.data_access import DEBUG, DataType, access_point, utils_log

message_existence = {
    "user": lambda update: update.effective_user is None,
    "message": lambda update: update.effective_message is None,
    "text": lambda update: update.effective_message.text is None,
    "caption": lambda update: update.effective_message.caption is None,
    "voice": lambda update: update.effective_message.voice is None,
    "video_note": lambda update: update.effective_message.video_note is None,
    "photo": lambda update: update.effective_message.photo is None
}

group_chat_commands = list()
group_admins_commands = list()
handlers_list = list()
job_queue = JobQueue()

async def set_up_job_queue(appl: Application):
    job_queue.set_application(appl)
    await job_queue.start()
    utils_log.info("Очередь задач запущена")

def register_command(level: int, desc: str):
    def wrapper(func):
        command = getattr(func, "__name__").replace('_command', '')
        if DEBUG:
            utils_log.info(f"Зарегистрировал хэндлер команды - {command} - {func}")
        handlers_list.append(CommandHandler(command, func))
        if level < 2: group_chat_commands.append(BotCommand(command, desc))
        if level < 3: group_admins_commands.append(BotCommand(command, desc))
        return func
    return wrapper

def register_callback_handler(cond):
    def wrapper(func):
        if DEBUG:
            utils_log.info(f"Зарегистрировал хэндлер обратного запроса - {func}")
        handlers_list.append(CallbackQueryHandler(func, cond))
        return func
    return wrapper

def register_message_handler(message_filter):
    def wrapper(func):
        if DEBUG:
            utils_log.info(f"Зарегистрировал хэндлер сообщений - {func}")
        handlers_list.append(MessageHandler(message_filter, func))
        return func
    return wrapper

def register_chat_member_handler(who):
    def wrapper(func):
        if DEBUG:
            utils_log.info(f"Зарегистрировал хэндлер участника - {func}")
        handlers_list.append(ChatMemberHandler(func, who))
        return func
    return wrapper

def register_job(interval):
    def wrapper(func):
        if DEBUG:
            utils_log.info(f"Зарегистрировал хэндлер задачи - {func}")
        job_queue.run_once(func, interval)
        return func
    return wrapper

def register_job_repeating(interval):
    def wrapper(func):
        if DEBUG:
            utils_log.info(f"Зарегистрировал хэндлер повторяемой задачи - {func}")
        job_queue.run_repeating(func, interval)
        return func
    return wrapper

def skip_filtered_updates(handler):
    @wraps(handler)
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

def check_if_message_exists(argument: str):
    def check(handler):
        @wraps(handler)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.message is None or message_existence[argument](update):
                return None
            return await handler(update, context)
        return wrapper
    return check

def status_check(handler):
    @wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_member = await context.bot.get_chat_member(
            update.effective_chat.id, update.effective_user.id
        )
        if chat_member.status not in {"administrator", "owner"}:
            await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
            return None

        return await handler(update, context)
    return wrapper

def argument_check(message: str):
    def check(handler):
        @wraps(handler)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if not context.args:
                await update.message.reply_text(message)
                return None

            return await handler(update, context)
        return wrapper
    return check