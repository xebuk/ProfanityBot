from datetime import datetime, time
from random import randint

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.analysis import Messages
from core.data_access import DataType, access_point

from .handler_utils import register_callback_handler, skip_filtered_updates, \
    register_command, status_check, argument_check

top_arguments = {
    "curse" : (
        Messages.TOP_CURSE,
        (DataType.CURSES,),
        False,
        Messages.TOP_CURSE_EVERYONE_IS_POLITE,
        lambda entry: entry,
        lambda entry: (entry[2], entry[0])
    ),
    "curse_delta" : (
        Messages.TOP_CURSE_REFRESH,
        (DataType.CURSES_DELTA,),
        False,
        Messages.REGULAR_TOP_ALL_POLITE,
        lambda entry: entry,
        lambda entry: (entry[2], entry[0])
    ),
    "curse_percentage" : (
        Messages.TOP_CURSE,
        (DataType.CURSES, DataType.MESSAGE_COUNTER),
        False,
        Messages.TOP_CURSE_EVERYONE_IS_POLITE,
        lambda entry: (entry[0], entry[1], entry[2] / entry[3]),
        lambda entry: (entry[2] / entry[3], entry[0])
    ),
    "troll" : (
        Messages.TOP_TROLLING,
        (DataType.TROLLS,),
        False,
        Messages.TOP_TROLLING_NO_CLOWN,
        lambda entry: entry,
        lambda entry: (entry[2], entry[0])
    ),
    "shots" : (
        Messages.TOP_SHOTS,
        (DataType.MAX_SHOTS,),
        True,
        Messages.TOP_SHOTS_EVERYONE_ARE_ALIVE,
        lambda entry: entry,
        lambda entry: (entry[2], entry[0])
    )
}

top_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("Проклятия (коэффициент)", callback_data="curse_percentage")],
    [InlineKeyboardButton("Проклятия", callback_data="curse"), InlineKeyboardButton("Проклятия (за период)", callback_data="curse_delta")],
    [InlineKeyboardButton("Троллинг", callback_data="troll"), InlineKeyboardButton("Выстрелы", callback_data="shots")]
])

@register_callback_handler(lambda query: query in top_arguments.keys())
@skip_filtered_updates
async def top_clicked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    (start_message, data_types,
     in_reverse, nothing_message,
     map_lambda, sort_lambda) = top_arguments[update.callback_query.data]

    message = start_message
    top = list(map(map_lambda, sorted(
        access_point.get_data_from_chat(
            update.effective_chat.id,
            [DataType.USER_ID, DataType.USER_NAME, *data_types],
            None,
            [*data_types], True,
            False
        ),
        key=sort_lambda, reverse=in_reverse
    )))

    index = 1
    summ = 0
    for i in range(len(top)):
        if top[i][2] == 0:
            continue
        message += Messages.TOP_ENTRY.format(index, top[i][1], top[i][2])
        summ += top[i][2]
        index += 1
    try:
        if message == start_message:
            await update.callback_query.edit_message_text(
                nothing_message,
                reply_markup=top_buttons
            )
        else:
            message += Messages.TOP_RESULT.format(round(summ, 2))
            await update.callback_query.edit_message_text(
                message,
                reply_markup=top_buttons
            )
    except Exception as e:
        pass

async def last_top_before_reset(update: Update, top_type: str):
    (start_message, data_types,
     in_reverse, nothing_message,
     map_lambda, sort_lambda) = top_arguments[update.callback_query.data]

    message = start_message
    top = list(map(map_lambda, sorted(
        access_point.get_data_from_chat(
            update.effective_chat.id,
            [DataType.USER_ID, DataType.USER_NAME, *data_types],
            None,
            [*data_types], True,
            False
        ),
        key=sort_lambda, reverse=in_reverse
    )))

    index = 1
    summ = 0
    for i in range(len(top)):
        if top[i][2] == 0:
            continue
        message += Messages.TOP_ENTRY.format(index, top[i][1], top[i][2])
        summ += top[i][2]
        index += 1
    try:
        if message == start_message:
            await update.message.reply_text(nothing_message)
        else:
            message += Messages.TOP_RESULT.format(round(summ, 2))
            await update.message.reply_text(message)
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


@skip_filtered_updates
async def lull_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now()
    week_day = now.weekday()
    day_time = now.time()

    if time(0) <= day_time < time(3):
        match week_day:
            case 0: await update.message.reply_text("Лучше иди спать, начало недели уже наступило.")
            case 1: await update.message.reply_text("Середина недели пока не наступила, давай шуруй спать.")
            case 2: await update.message.reply_text("Да, среда - маленькая пятница, но спать тоже надо.")
            case 3: await update.message.reply_text("Родной, уже четверг наступил, иди спи.")
            case 4: await update.message.reply_text("Давай, сегодня последний день из будней на этой неделе, иди спать.")
            case _: await update.message.reply_text("Родной, это выходной, делай что хочешь.")
        # await update.message.reply_text("Ну, лучше поздно, чем никогда. Спокойной ночи.")
    elif time(3) <= day_time < time(6):
        match week_day:
            case 0: await update.message.reply_text("Лучше иди спать, начало недели уже наступило.")
            case 1: await update.message.reply_text("Середина недели пока не наступила, давай шуруй спать.")
            case 2: await update.message.reply_text("Да, среда - маленькая пятница, но спать тоже надо.")
            case 3: await update.message.reply_text("Родной, уже четверг наступил, иди спи.")
            case 4: await update.message.reply_text("🫡")
            case _: await update.message.reply_text("Родной, это выходной, делай что хочешь.")
        # await update.message.reply_text("Тут уже лучше дождаться утра, чем спать. Давай, держись.")
    elif time(6) <= day_time < time(18):
        await update.message.reply_text("Ты точно сейчас спать хочешь?")
    elif time(18) <= day_time < time(22):
        await update.message.reply_text("Чем раньше сон, тем раньше утро! Спокойной ночи!")
    else:
        await update.message.reply_text("Спокойной ночи.")

@register_command(2, "Изменяет количество обсценной лексики указанного пользователя на указанное число")
@status_check
@skip_filtered_updates
async def change_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        callback = access_point.change_curses_username(
            update.message.chat_id,
            context.args[0],
            int(context.args[1])
        )
        if callback:
            await update.message.reply_text(Messages.CHANGE_CURSE_SUCCESS)
        else:
            await update.message.reply_text(Messages.CHANGE_CURSE_FAILURE)
    except IndexError:
        await update.message.reply_text(Messages.NOT_ENOUGH_ARGUMENTS)

@register_command(2, "Сбрасывает рейтинг обсценной лексики или рейтинг троллинга от бота")
@status_check
@skip_filtered_updates
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.args[0] in {"curse", "troll"}:
            await last_top_before_reset(update, context.args[0])
            access_point.reset_chat(update.message.chat_id, f"{context.args[0]}s")
            await update.message.reply_text(Messages.RESET)
        else:
            await update.message.reply_text(Messages.RESET_ACCIDENT)
    except IndexError:
        await update.message.reply_text(Messages.NOT_ENOUGH_ARGUMENTS)

@register_command(2, "Изменяет ссылку для доната на указанный текст в аргументах")
@argument_check(Messages.DONATE_CHANGE_NOTHING)
@status_check
@skip_filtered_updates
async def set_donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
@status_check
@skip_filtered_updates
async def random_send_permit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    changed, permit = access_point.change_random_send_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(Messages.RANDOM_SEND_SUCCESS.format(result))
    else:
        await update.message.reply_text(Messages.RANDOM_SEND_FAILURE)

@register_command(2, "Изменяет сообщение для случайной отправки на указанное в аргументах")
@argument_check(Messages.RANDOM_SEND_MESSAGE_NOTHING)
@status_check
@skip_filtered_updates
async def set_random_send_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
@status_check
@skip_filtered_updates
async def trolling_permit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
@status_check
@skip_filtered_updates
async def regular_curse_update_permit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    changed, permit = access_point.change_regular_curse_update_status(update.message.chat_id)
    if changed:
        result = "Нет" if permit == 1 else "Да"
        await update.message.reply_text(Messages.REGULAR_TOP_SUCCESS.format(result))
    else:
        await update.message.reply_text(Messages.REGULAR_TOP_FAILURE)

@register_command(2, "Изменяет порог количества мата, от которого бот отправит уведомление.")
@argument_check(Messages.CURSE_THRESHOLD_NOTHING)
@status_check
@skip_filtered_updates
async def curse_threshold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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