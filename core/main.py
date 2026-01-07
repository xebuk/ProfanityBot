from telegram import BotCommandScopeAllChatAdministrators, \
    BotCommandScopeAllGroupChats
from telegram.ext import Application

from core.analysis import Messages
from core.data_access import BOT_TOKEN, SILENT, graceful_exit, \
    DataType, access_point, main_body_log
from core.IO import *

async def broadcast_to_all_chats(appl: Application, text: str):
    chat_ids = access_point.get_data_from_main_table(
        [DataType.CHAT_ID],
        [DataType.QUIET_MODE, DataType.IS_ACTIVE],
        None,
        False, False,
        0, 1
    )

    if not SILENT:
        for chat_id in chat_ids:
            await appl.bot.send_message(chat_id=chat_id[0], text=text, disable_notification=True)

async def on_start(appl: Application):
    job_queue.set_application(appl)
    await job_queue.start()
    main_body_log.info("Очередь задач запущена")

    await appl.bot.set_my_commands(
        group_chat_commands,
        scope=BotCommandScopeAllGroupChats()
    )
    await appl.bot.set_my_commands(
        group_admins_commands,
        scope=BotCommandScopeAllChatAdministrators()
    )

    await broadcast_to_all_chats(appl, Messages.I_AWAKE)

async def on_stop(appl: Application):
    graceful_exit()
    await broadcast_to_all_chats(appl, Messages.I_SLEEP)
    access_point.shutdown()

app = (
    Application.builder()
    .token(BOT_TOKEN)
    .post_init(on_start)
    .post_stop(on_stop)
    .build()
)

app.add_handlers(preprocessing_handlers, group=0)
app.add_handlers(handlers_list, group=1)

if __name__ == "__main__":
    app.run_polling(
        close_loop=False
    )