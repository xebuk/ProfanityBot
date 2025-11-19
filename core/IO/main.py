from telegram import BotCommandScopeAllChatAdministrators, BotCommandScopeAllGroupChats
from telegram.ext import Application, MessageHandler, filters, ContextTypes, \
    CommandHandler, ChatMemberHandler, JobQueue

from random import randint

from core.data_access.config import BOT_TOKEN
from core.IO.handle_commands import group_chat_commands, group_admins_commands, \
    top_curse_command, top_troll_command, change_curse_command, reset_command, \
    all_command, set_donation_link, donation_link_command, \
    permit_to_random_send_command, set_random_send_message, permit_to_troll_command
from core.IO.handle_functions import handle_message, handle_caption, \
    handle_voice_message, handle_video_note, handle_other_join
from core.data_access.database import access_point, DataType
from core.data_access.logs import main_body_log

async def random_send(context: ContextTypes.DEFAULT_TYPE):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID, DataType.RANDOM_SEND_MESSAGE],
        [DataType.IS_PERMITTED_TO_RANDOM_SEND],
        None,
        False, False,
        1
    )
    for chat_id, message in chat_ids:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message, disable_notification=True)
            main_body_log.info(f"Случайное сообщение было отправлено в {chat_id}")
        except Exception as e:
            main_body_log.info(f"Случайное сообщение не было отправлено в {chat_id}: {e}")

    app.job_queue.run_once(random_send, randint(3600, 21600))

job_queue = JobQueue()

async def on_start(appl: Application):
    job_queue.set_application(appl)
    await job_queue.start()
    job_queue.run_once(random_send, randint(3600, 14400))

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
        await appl.bot.send_message(chat_id=chat_id[0], text="я проснулся", disable_notification=True)

async def on_stop(appl: Application):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        None,
        None,
        False, False
    )
    for chat_id in chat_ids:
        await appl.bot.send_message(chat_id=chat_id[0], text="я пошел спать", disable_notification=True)

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .read_timeout(30)
    .write_timeout(30)
    .connect_timeout(30)
    .pool_timeout(30)
    .post_init(on_start)
    .post_stop(on_stop)
    .build()
)

def main():
    app.add_handler(CommandHandler("curse", top_curse_command))
    app.add_handler(CommandHandler("change_curse", change_curse_command))
    app.add_handler(CommandHandler("troll", top_troll_command))
    app.add_handler(CommandHandler("reset", reset_command))
    app.add_handler(CommandHandler("all", all_command))
    app.add_handler(CommandHandler("set_donate", set_donation_link))
    app.add_handler(CommandHandler("donate", donation_link_command))
    app.add_handler(CommandHandler("random_send_permit", permit_to_random_send_command))
    app.add_handler(CommandHandler("set_random_send_message", set_random_send_message))
    app.add_handler(CommandHandler("trolling_permit", permit_to_troll_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & ~filters.CAPTION, handle_message))
    app.add_handler(MessageHandler(filters.CAPTION & ~filters.COMMAND, handle_caption)),
    app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
    app.add_handler(MessageHandler(filters.VIDEO_NOTE, handle_video_note))

    app.add_handler(ChatMemberHandler(handle_other_join, ChatMemberHandler.CHAT_MEMBER))

    app.run_polling()

if __name__ == "__main__":
    main()
