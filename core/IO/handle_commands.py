from random import randint

from telegram import Update, InlineKeyboardButton, \
    InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.analysis.messages import Messages
from core.IO.handle_functions import skip_filtered_updates, register_command, \
    register_callback_handler
from core.data_access.database import access_point, DataType

top_arguments = {
    "curse" : (Messages.TOP_CURSE, DataType.CURSES, False, Messages.TOP_CURSE_EVERYONE_IS_POLITE),
    "curse_delta" : (Messages.TOP_CURSE_REFRESH, DataType.CURSES_DELTA, False, Messages.REGULAR_TOP_ALL_POLITE),
    "troll" : (Messages.TOP_TROLLING, DataType.TROLLS, False, Messages.TOP_TROLLING_NO_CLOWN),
    "shots" : (Messages.TOP_SHOTS, DataType.MAX_SHOTS, True, Messages.TOP_SHOTS_EVERYONE_ARE_ALIVE)
}

top_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("Проклятия", callback_data="curse"), InlineKeyboardButton("Проклятия (за период)", callback_data="curse_delta")],
    [InlineKeyboardButton("Троллинг", callback_data="troll"), InlineKeyboardButton("Выстрелы", callback_data="shots")]
])

@register_callback_handler(lambda query: query in top_arguments.keys())
@skip_filtered_updates
async def top_clicked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_parameters = top_arguments[update.callback_query.data]

    message = current_parameters[0]
    top = sorted(
        access_point.get_data_from_chat(
            update.effective_chat.id,
            [DataType.USER_ID, DataType.USER_NAME, current_parameters[1]],
            None,
            [current_parameters[1]], True,
            False
        ),
        key=lambda x: (x[2], x[0]), reverse=current_parameters[2]
    )

    index = 1
    summ = 0
    for i in range(len(top)):
        if top[i][2] == 0:
            continue
        message += Messages.TOP_ENTRY.format(index, top[i][1], top[i][2])
        summ += top[i][2]
        index += 1
    try:
        if message == current_parameters[0]:
            await update.callback_query.edit_message_text(
                current_parameters[3],
                reply_markup=top_buttons
            )
        else:
            message += Messages.TOP_RESULT.format(summ)
            await update.callback_query.edit_message_text(
                message,
                reply_markup=top_buttons
            )
    except Exception as e:
        pass

@register_command(1, "Выводит рейтинг по всему чату")
@skip_filtered_updates
async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Выберите топ:",
        reply_markup=top_buttons
    )

@register_command(1, "Выводит ссылку на донат")
@skip_filtered_updates
async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    donation_link = str(access_point.get_data_from_main_table(
        [DataType.DONATION_LINK],
        [DataType.CHAT_ID],
        None,False,
        True,
        update.message.chat_id
    )[0])
    await update.message.reply_text(donation_link)

@register_command(1, "Играет Русскую Рулетку")
@skip_filtered_updates
async def shoot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shot = randint(1, 6)
    ready = randint(1, 6)

    access_point.change_shots(
        update.effective_chat.id,
        update.effective_user.id,
        shot == ready
    )
    if shot == ready:
        await update.effective_message.reply_text(Messages.SHOOT_FAILURE)
    else:
        await update.effective_message.reply_text(Messages.SHOOT_SUCCESS)

@register_command(1, "Аналог @all в Дискорде, отмечает всех в чате")
@skip_filtered_updates
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = Messages.ALERT

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
    message += Messages.THANKS_FOR_ALERT
    await update.message.reply_text(message)

@register_command(2, "Изменяет количество обсценной лексики указанного пользователя на указанное число")
@skip_filtered_updates
async def change_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
        return

    if context.args[0] and context.args[1]:
        callback = access_point.change_curses_username(
            update.message.chat_id,
            context.args[0],
            int(context.args[1])
        )
        if callback:
            await update.message.reply_text(Messages.CHANGE_CURSE_SUCCESS)
        else:
            await update.message.reply_text(Messages.CHANGE_CURSE_FAILURE)

@register_command(2, "Сбрасывает рейтинг обсценной лексики и рейтинг троллинга от бота")
@skip_filtered_updates
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )

    if chat_member.status in {"administrator", "owner"} and context.args[0] in {"curses", "trolls"}:
        access_point.reset_chat(update.message.chat_id, context.args[0])
        await update.message.reply_text(Messages.RESET)
    elif chat_member.status in {"administrator", "owner"}:
        await update.message.reply_text(Messages.RESET_ACCIDENT)
    else:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)

@register_command(2, "Изменяет ссылку для доната на указанный текст в аргументах")
@skip_filtered_updates
async def set_donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
        return

    if not context.args:
        await update.message.reply_text(Messages.DONATE_CHANGE_NOTHING)
        return

    access_point.update_data_from_main_table(
        [DataType.DONATION_LINK],
        [DataType.CHAT_ID],
        " ".join(context.args), update.message.chat_id
    )
    await update.message.reply_text(Messages.DONATE_CHANGE_SUCCESS)

@register_command(2,
"""
Переключает разрешение на случайную отправку сообщений от бота.
При включении бот будет со случайными промежутками от часа до 4 отправлять указанное сообщение.
""")
@skip_filtered_updates
async def random_send_permit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
        return

    changed, permit = access_point.change_random_send_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(Messages.RANDOM_SEND_SUCCESS.format(result))
    else:
        await update.message.reply_text(Messages.RANDOM_SEND_FAILURE)

@register_command(2, "Изменяет сообщение для случайной отправки на указанное в аргументах")
@skip_filtered_updates
async def set_random_send_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
        return

    if not context.args:
        await update.message.reply_text(Messages.RANDOM_SEND_MESSAGE_NOTHING)
        return

    access_point.update_data_from_main_table(
        [DataType.RANDOM_SEND_MESSAGE],
        [DataType.CHAT_ID],
        " ".join(context.args), update.message.chat_id
    )
    await update.message.reply_text(Messages.RANDOM_SEND_MESSAGE_SUCCESS)

@register_command(2,
"""
Переключает разрешение на троллинг от бота.
При включении бот будет отмечать случайные сообщения реакцией 🤡
""")
@skip_filtered_updates
async def trolling_permit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
        return

    changed, permit = access_point.change_trolling_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(Messages.TROLL_SUCCESS.format(result))
    else:
        await update.message.reply_text(Messages.TROLL_FAILURE)

@register_command(2,
"""
Переключает разрешение на регулярный отчет по обсценной лексике.
При включении бот будет регулярно (каждые 4 часа) отправлять отчеты по мату внутри сообщений.
""")
@skip_filtered_updates
async def regular_curse_update_permit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
        return

    changed, permit = access_point.change_regular_curse_update_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(Messages.REGULAR_TOP_SUCCESS.format(result))
    else:
        await update.message.reply_text(Messages.REGULAR_TOP_FAILURE)

@register_command(2, "Изменяет порог количества мата, от которого бот отправит уведомление.")
@skip_filtered_updates
async def curse_threshold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = await context.bot.get_chat_member(
        update.message.chat_id, update.message.from_user.id
    )
    if chat_member.status not in {"administrator", "owner"}:
        await update.message.reply_text(Messages.NOT_HIGH_ENOUGH_STATUS)
        return

    if not context.args:
        await update.message.reply_text(Messages.CURSE_THRESHOLD_NOTHING)
        return

    try:
        counter = int(context.args[0])
        access_point.update_data_from_main_table(
            [DataType.CURSE_THRESHOLD],
            [DataType.CHAT_ID],
            counter, update.effective_chat.id
        )
        await update.message.reply_text(Messages.CURSE_THRESHOLD_SUCCESS)
    except Exception as e:
        access_point.add_new_chat(update.effective_chat.id)
        await update.message.reply_text(Messages.CURSE_THRESHOLD_FAILURE)