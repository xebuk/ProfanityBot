from telegram import Update
from telegram.ext import ContextTypes, filters, MessageHandler, \
    ApplicationHandlerStop

from core.analysis import Messages
from core.data_access import access_point, DataType, prep_log, DEBUG

from .handle_functions import act_on_letter
from .handler_utils import restricted_access_filter

async def handle_private_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        Messages.PRIVATE_MESSAGES
    )
    raise ApplicationHandlerStop()

async def handle_restricted_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids_on_queue = set(
        i[0] for i in access_point.get_data_from_queue(
            [DataType.CHAT_ID], False
        )
    )

    if update.effective_chat.id not in chat_ids_on_queue:
        await update.effective_message.reply_text(
            Messages.UNREGISTERED_CHAT
        )
        access_point.insert_data_into_queue(
            update.effective_chat.id,
            update.effective_chat.effective_name
        )
    raise ApplicationHandlerStop()

async def handle_non_bot_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if DEBUG:
        prep_log.info("Прошел в обработку сообщения")
    await act_on_letter(update.effective_message)

preprocessing_handlers = [
    MessageHandler(filters.ChatType.PRIVATE, handle_private_messages),
    MessageHandler(restricted_access_filter, handle_restricted_access),
    MessageHandler(~filters.VIA_BOT, handle_non_bot_update)
]

prep_log.info("Зарегистрировал все хэндлеры предварительной обработки")