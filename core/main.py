from telegram import BotCommandScopeAllChatAdministrators, \
    BotCommandScopeAllGroupChats
from telegram.ext import Application

from core.analysis import Messages
from core.data_access import BOT_TOKEN, SILENT, graceful_exit, \
    DataType, access_point
from core.IO import *

async def on_start(appl: Application):
    await set_up_job_queue(appl)

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

    if not SILENT:
        for chat_id in chat_ids:
            await appl.bot.send_message(chat_id=chat_id[0], text=Messages.I_AWAKE, disable_notification=True)

async def on_stop(appl: Application):
    graceful_exit()

    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        None,
        None,
        False, False
    )

    if not SILENT:
        for chat_id in chat_ids:
            await appl.bot.send_message(chat_id=chat_id[0], text=Messages.I_SLEEP, disable_notification=True)

    access_point.shutdown()

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(on_start)
    .post_stop(on_stop)
    .build()
)

for handler in handlers_list:
    app.add_handler(handler)

if __name__ == "__main__":
    app.run_polling(
        close_loop=False
    )