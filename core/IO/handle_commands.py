from telegram import Update, BotCommand
from telegram.ext import ContextTypes

from core.IO.handle_functions import skip_filtered_updates
from core.data_access.database import access_point, DataType

group_chat_commands = [
    BotCommand(
        "curse",
        "Выводит рейтинг по обсценной лексике среди всего чата"
    ),
    BotCommand(
        "troll",
        "Выводит рейтинг по троллингу от бота среди всего чата"
    ),
    BotCommand(
        "all",
        "Аналог @all в Дискорде, отмечает всех в чате"
    ),
    BotCommand(
        "donate",
        "Выводит ссылку на донат"
    )
]
group_admins_commands = [
    BotCommand(
        "curse",
        "Выводит рейтинг по обсценной лексике среди всего чата"
    ),
    BotCommand(
        "troll",
        "Выводит рейтинг по троллингу от бота среди всего чата"
    ),
    BotCommand(
        "all",
        "Аналог @all в Дискорде, отмечает всех в чате"
    ),
    BotCommand(
        "donate",
        "Выводит ссылку на донат"
    ),
    BotCommand(
        "change_curse",
        "Изменяет количество обсценной лексики указанного пользователя на указанное число"
    ),
    BotCommand(
        "reset",
        "Сбрасывает рейтинг обсценной лексики и рейтинг троллинга от бота"
    ),
    BotCommand(
        "set_donate",
        "Изменяет ссылку для доната на указанный текст в аргументах"
    ),
    BotCommand(
        "random_send_permit",
        """Переключает разрешение на случайную отправку сообщений от бота.
        При включении бот будет со случайными промежутками от часа до 4 отправлять указанное сообщение.
        """
    ),
    BotCommand(
        "set_random_send_message",
        "Изменяет сообщение для случайной отправки на указанное в аргументах"
    ),
    BotCommand(
        "trolling_permit",
        """Переключает разрешение на троллинг от бота.
        При включении бот будет отмечать случайные сообщения реакцией 🤡
        """
    )
]

@skip_filtered_updates
async def top_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Список из ада: \n"
    top = sorted(
        access_point.get_data_from_chat(
            update.message.chat_id,
            [DataType.USER_ID, DataType.USER_NAME, DataType.CURSES],
            None,
            [DataType.CURSES], True,
            False
        ),
        key=lambda x: (x[2], x[0])
    )

    index = 1
    summ = 0
    for i in range(len(top)):
        if top[i][2] == 0:
            continue
        message += f"{index}: {top[i][1]} - {top[i][2]}\n"
        summ += top[i][2]
        index += 1
    if message == "Список из ада: \n":
        await update.message.reply_text("Пока все ангелочки)")
    else:
        message += f"Итого: {summ}"
        await update.message.reply_text(message)

@skip_filtered_updates
async def top_troll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "Список из клоунской: \n"
    top = sorted(
        access_point.get_data_from_chat(
            update.message.chat_id,
            [DataType.USER_ID, DataType.USER_NAME, DataType.TROLLS],
            None,
            [DataType.TROLLS], True,
            False
        ),
        key=lambda x: (x[2], x[0])
    )

    index = 1
    summ = 0
    for i in range(len(top)):
        if top[i][2] == 0:
            continue
        message += f"{index}: {top[i][1]} - {top[i][2]}\n"
        summ += top[i][2]
        index += 1
    if message == "Список из клоунской: \n":
        await update.message.reply_text("Пока все хороши)")
    else:
        message += f"Итого: {summ}"
        await update.message.reply_text(message)

@skip_filtered_updates
async def change_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    if context.args[0] and context.args[1]:
        callback = access_point.change_curses_username(
            update.message.chat_id,
            context.args[0],
            int(context.args[1])
        )
        if callback:
            await update.message.reply_text("Рейтинг изменен успешно.")
        else:
            await update.message.reply_text("Не удалось изменить рейтинг. Попробуйте позже.")

@skip_filtered_updates
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )

    if chat_member.status in {"administrator", "owner"} and context.args:
        access_point.reset_chat(update.message.chat_id)
        await update.message.reply_text("Сброс данных произведен успешно.")
    elif chat_member.status in {"administrator", "owner"}:
        await update.message.reply_text("Для предотвращения случайного сброса для работы команды надо ввести любой аргумент.")
    else:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")

@skip_filtered_updates
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "ВНИМАНИЕ!\n"

    all_user_names = sorted(
        access_point.get_data_from_chat(
            update.message.chat_id,
            [DataType.USER_NAME],
            None,
            None, False,
            False
        ),
        key=lambda x: x[0].lower()
    )
    for i in all_user_names:
        message += f"{i[0]}\n"
    message += "Спасибо за внимание."
    await update.message.reply_text(message)

@skip_filtered_updates
async def set_donation_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    if not context.args:
        await update.message.reply_text("Вы не ввели ссылку для доната!")
        return

    access_point.update_data_from_main_table(
        [DataType.DONATION_LINK],
        [DataType.CHAT_ID],
        " ".join(context.args), update.message.chat_id
    )

@skip_filtered_updates
async def donation_link_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    donation_link = str(access_point.get_data_from_main_table(
        [DataType.DONATION_LINK],
        [DataType.CHAT_ID],
        None,False,
        True,
        update.message.chat_id
    )[0])
    await update.message.reply_text(donation_link)

@skip_filtered_updates
async def permit_to_random_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    changed, permit = access_point.change_random_send_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(f"Статус случайной отправки в данный чат изменен на {result}")
    else:
        await update.message.reply_text(f"Статус случайной отправки в данный чат не был изменен. Попробуйте ещё раз.")

@skip_filtered_updates
async def set_random_send_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text("У вас недостаточно прав доступа в данном чате.")
        return

    if not context.args:
        await update.message.reply_text("Вы не ввели сообщение для случайной отправки!")
        return

    access_point.update_data_from_main_table(
        [DataType.RANDOM_SEND_MESSAGE],
        [DataType.CHAT_ID],
        " ".join(context.args), update.message.chat_id
    )
    await update.message.reply_text("Сообщение успешно изменено!")

@skip_filtered_updates
async def permit_to_troll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(
            "У вас недостаточно прав доступа в данном чате.")
        return

    changed, permit = access_point.change_trolling_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(f"Статус троллинга от бота для данного чата изменен на {result}")
    else:
        await update.message.reply_text(f"Статус троллинга от бота для данного чата не был изменен. Попробуйте ещё раз.")