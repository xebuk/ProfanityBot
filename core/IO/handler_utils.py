from collections import defaultdict
from datetime import timedelta
from functools import wraps

from telegram import Update, BotCommand, MessageOriginUser, MessageOriginChat, \
    MessageOriginChannel, MessageOriginHiddenUser
from telegram.ext import MessageHandler, ChatMemberHandler, ContextTypes, \
    CallbackQueryHandler, JobQueue, CommandHandler
from telegram.ext.filters import UpdateFilter

from core.analysis import Messages
from core.data_access import DEBUG, utils_log, access_point, DataType

message_existence = {
    "user": lambda update: update.effective_user is None,
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
        handlers_list.append(MessageHandler(message_filter & ignore_some_forwarded_filter, func))
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

def check_if_message_exists(argument: str):
    def check(handler):
        @wraps(handler)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_message is None or message_existence[argument](update):
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

class ForwardFromOtherFilter(UpdateFilter):
    def __init__(self):
        super().__init__("ForwardFromOtherFilter", False)

    def filter(self, update: Update):
        current_message = update.message or update.channel_post
        if not current_message or current_message.forward_origin is None:
            return True

        origin = current_message.forward_origin
        sender = update.effective_user

        if isinstance(origin, MessageOriginUser):
            return sender.id != origin.sender_user.id
        elif isinstance(origin, (
            MessageOriginChat, MessageOriginChannel, MessageOriginHiddenUser
        )):
            return False

        return True

ignore_some_forwarded_filter = ForwardFromOtherFilter()

class RestrictedAccessFilter(UpdateFilter):
    def __init__(self):
        super().__init__("RestrictedAccessFilter", False)

    def filter(self, update: Update):
        chat_ids = set(
            i[0] for i in access_point.get_data_from_main_table(
                [DataType.CHAT_ID], None, None, False, False
            )
        )

        return update.effective_chat.id not in chat_ids

restricted_access_filter = RestrictedAccessFilter()

class EditedMessageFilter(UpdateFilter):
    def __init__(self):
        super().__init__("EditedMessageFilter", False)

    def filter(self, update: Update):
        return update.edited_message is not None

edited_message_filter = EditedMessageFilter()

two_hours_ago = timedelta(hours=2)
last_day = timedelta(days=1)
seven_days_ago = timedelta(days=7)
month_ago = timedelta(days=31)
year_ago = timedelta(days=365)

def transform_event_data(event_group: tuple, event_data: list):
    valid_events = set(event_group)
    data_dict = defaultdict(dict)

    for user_id, user_name, event_type, amount in event_data:
        if event_type in valid_events:
            data_dict[(user_id, user_name)][event_type] = amount

    result = []
    for user_id, user_name in sorted(data_dict.keys()):
        if valid_events.difference(data_dict[(user_id, user_name)].keys()):
            continue
        row = [user_id, user_name]
        for event_type in event_group:
            row.append(data_dict[(user_id, user_name)].get(event_type, None))
        result.append(tuple(row))

    return result