from telegram import Update
from telegram.ext import filters, ContextTypes

from core.data_access import access_point

from .handle_functions import act_on_text, handle_audio
from .handler_utils import register_message_handler, check_if_message_exists, \
    edited_message_filter, register_chat_member_handler

@register_message_handler(filters.CAPTION)
@check_if_message_exists("caption")
async def handle_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await act_on_text(update.effective_message.caption, update.effective_message)

@register_message_handler(edited_message_filter & filters.CAPTION)
@check_if_message_exists("caption")
async def handle_edited_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await act_on_text(update.effective_message.text, update.effective_message)

@register_message_handler(filters.TEXT)
@check_if_message_exists("text")
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await act_on_text(update.effective_message.text, update.effective_message)

@register_message_handler(edited_message_filter & filters.TEXT)
@check_if_message_exists("text")
async def handle_edited_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await act_on_text(update.effective_message.text, update.effective_message)

@register_message_handler(filters.VOICE)
@check_if_message_exists("voice")
async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_audio(update.effective_message.voice, update.effective_message)

@register_message_handler(filters.VIDEO_NOTE)
@check_if_message_exists("video_note")
async def handle_video_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_audio(update.effective_message.video_note, update.effective_message)

@register_chat_member_handler(0)
@check_if_message_exists("user")
async def handle_other_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    access_point.add_or_update_name(
        update.effective_chat.id,
        update.effective_user.id,
        update.effective_user.name
    )