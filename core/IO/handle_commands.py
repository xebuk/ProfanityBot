from datetime import timedelta, datetime
from random import randint

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from core.analysis import Messages
from core.data_access import DataType, access_point

from .handler_utils import register_callback_handler, register_command, \
    status_check, argument_check, transform_event_data, year_ago

top_arguments = {
    "curse" : (
        Messages.TOP_CURSE,
        Messages.TOP_CURSE_EVERYONE_IS_POLITE,
        ("curse",),
        "sum",
        False,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    ),
    "curse_percentage_messages" : (
        Messages.TOP_CURSE_MESSAGES,
        Messages.TOP_CURSE_EVERYONE_IS_POLITE,
        ("curse", "message"),
        "sum",
        False,
        lambda entry: (entry[1], entry[2] / entry[3]),
        lambda entry: (entry[2] / entry[3], entry[0])
    ),
    "curse_percentage_words" : (
        Messages.TOP_CURSE_WORDS,
        Messages.TOP_CURSE_EVERYONE_IS_POLITE,
        ("curse", "word"),
        "sum",
        False,
        lambda entry: (entry[1], entry[2] / entry[3]),
        lambda entry: (entry[2] / entry[3], entry[0])
    ),
    "troll" : (
        Messages.TOP_TROLLING,
        Messages.TOP_TROLLING_NO_CLOWN,
        ("troll",),
        "sum",
        False,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    ),
    "shots" : (
        Messages.TOP_SHOTS,
        Messages.TOP_SHOTS_EVERYONE_ARE_ALIVE,
        ("shot_fail",),
        "max",
        True,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    ),
    "shot_at" : (
        Messages.TOP_SHOT,
        Messages.TOP_SHOT_NO_BLOOD,
        ("shot_at",),
        "sum",
        False,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    ),
    "insomnia" : (
        Messages.TOP_INSOMNIA,
        Messages.TOP_INSOMNIA_EVERYONE_ASLEEP,
        ("insomnia",),
        "sum",
        False,
        lambda entry: (entry[1], entry[2]),
        lambda entry: (entry[2], entry[0])
    )
}

top_buttons = InlineKeyboardMarkup([
    [InlineKeyboardButton("Проклятия (отношение к сообщениям)", callback_data="curse_percentage_messages")],
    [InlineKeyboardButton("Проклятия (отношение к словам)", callback_data="curse_percentage_words")],
    [InlineKeyboardButton("Проклятия", callback_data="curse"), InlineKeyboardButton("Троллинг", callback_data="troll"), InlineKeyboardButton("Бессонница", callback_data="insomnia")],
    [InlineKeyboardButton("Выстрелы", callback_data="shots"), InlineKeyboardButton("Мишени", callback_data="shot_at")]
])

def construct_top(chat_id: int, top_type: str, delta: timedelta):
    (start_message, nothing_message,
     event_group, amount_command, in_reverse,
     map_lambda, sort_lambda) = top_arguments[top_type]

    top = list(map(map_lambda, sorted(transform_event_data(
        event_group,
        access_point.pull_chat_wide_event(chat_id, amount_command, delta)
    ), key=sort_lambda, reverse=in_reverse)))

    message = start_message

    index = 0
    summ = 0
    previous_score = None

    for i in range(len(top)):
        if top[i][1] == 0:
            continue
        if top[i][1] != previous_score:
            previous_score = top[i][1]
            index += 1
        message += Messages.TOP_ENTRY.format(
            index, top[i][0], round(top[i][1], 2)
        )
        summ += top[i][1]

    if message == start_message:
        message = nothing_message
    else:
        message += Messages.TOP_RESULT.format(round(summ, 2))

    return message

def construct_help(command_arguments: dict):
    arguments = list()
    for item in sorted(list(command_arguments.items()), key=lambda x: x[1][0]):
        arguments.append(f"{item[0]} - {item[1][-1]}")
    return "Набор возможных аргументов: \n" + "\n".join(arguments)

@register_callback_handler(lambda query: query in top_arguments.keys())
async def top_clicked_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = construct_top(update.effective_chat.id, update.callback_query.data, year_ago)
    try:
        await update.callback_query.edit_message_text(
            message,
            reply_markup=top_buttons
        )
    except Exception as e:
        pass

@register_command(1, "Выводит рейтинг по всему чату")
async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Выберите топ:",
        reply_markup=top_buttons
    )

@register_command(1, "Выводит ссылку на донат")
async def donate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    donation_link = str(access_point.get_data_from_main_table(
        [DataType.DONATION_LINK],
        [DataType.CHAT_ID],
        None,False,
        True,
        update.effective_chat.id
    )[0])
    await update.effective_message.reply_text(donation_link)

@register_command(1,
"""
Играет Русскую Рулетку. При ответе на чье-либо сообщение стреляет в него (нужен активный high_noon).
"""
)
async def shoot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    high_noon_showdown_permit, shoot_bot_easter_egg = access_point.get_data_from_main_table(
        [DataType.HIGH_NOON_SHOWDOWN_PERMIT, DataType.SHOOT_BOT_EASTER_EGG],
        [DataType.CHAT_ID],
        None, False,
        True,
        update.effective_chat.id,
    )

    shot = randint(1, 6)
    ready = randint(1, 6)

    if update.effective_message.reply_to_message is None:
        current_shots = access_point.get_data_from_chat(
            update.effective_chat.id,
            [DataType.CURRENT_SHOTS],
            [DataType.USER_ID],
            None, False,
            True,
            update.effective_user.id
        )[0]

        if shot == ready:
            access_point.register_event(
                update.effective_chat.id,
                update.effective_user.id,
                "shot_fail", current_shots
            )
            access_point.update_data_from_chat(
                update.effective_chat.id,
                [DataType.CURRENT_SHOTS],
                [DataType.USER_ID],
                0, update.effective_user.id
            )
            await update.effective_message.reply_text(Messages.SHOOT_FAILURE)
        else:
            access_point.update_data_from_chat(
                update.effective_chat.id,
                [DataType.CURRENT_SHOTS],
                [DataType.USER_ID],
                current_shots + 1, update.effective_user.id
            )
            await update.effective_message.reply_text(Messages.SHOOT_SUCCESS)
    elif high_noon_showdown_permit == 1:
        bullet = access_point.get_data_from_chat(
            update.effective_chat.id,
            [DataType.BULLET_POSSESSION],
            [DataType.USER_ID],
            None, False,
            True,
            update.effective_user.id
        )[0]

        shot_message = update.effective_message.reply_to_message

        if shot_message.from_user.is_bot:
            shoot_bot_message = shoot_bot_easter_egg if shot == ready else "Дзынь!"
            await update.effective_message.reply_text(shoot_bot_message)
            return

        if bullet <= 0:
            await update.effective_message.reply_text("У вас нет пуль.")
            return

        access_point.register_event(
            update.effective_chat.id,
            shot_message.from_user.id,
            "shot_at", 1
        )
        access_point.update_data_from_chat(
            update.effective_chat.id,
            [DataType.BULLET_POSSESSION],
            [DataType.USER_ID],
            bullet - 1, update.effective_user.id
        )

        await shot_message.reply_text("В вас выстрелили!")

@register_command(1, "Аналог @all в Дискорде, отмечает всех в чате")
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = Messages.ALERT

    all_user_names = sorted(
        access_point.get_data_from_chat(
            update.effective_chat.id,
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
    await update.effective_message.reply_text(message)

@register_command(2, "Переключает режим сна")
@status_check
async def sleep_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    changed, permit = access_point.change_status(
        update.effective_chat.id,
        "quiet_night_mode"
    )
    if not changed:
        await update.effective_message.reply_text(Messages.NOT_GOOD_SLEEP)
        return

    access_point.update_data_from_main_table(
        [DataType.SLEEP_START_TIME],
        [DataType.CHAT_ID],
        datetime.now().isoformat(
            sep=" ",
            timespec="microseconds"
        ), update.effective_chat.id
    )

    all_user_names = sorted(
        access_point.get_data_from_chat(
            update.effective_chat.id,
            [DataType.USER_NAME],
            None,
            None, False,
            False
        ),
        key=lambda x: x[0].lower()
    )

    message = ""
    for i in all_user_names:
        message += f"{i[0]}\n"
    message += Messages.GOOD_SLEEP if permit == 1 else Messages.GOOD_AWAKENING
    await update.effective_message.reply_text(message)

@register_command(2, "Изменяет количество обсценной лексики указанного пользователя на указанное число")
@status_check
async def change_curse_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        callback = access_point.change_curses_username(
            update.effective_chat.id,
            context.args[0],
            int(context.args[1])
        )
        if callback:
            await update.effective_message.reply_text(Messages.CHANGE_CURSE_SUCCESS)
        else:
            await update.effective_message.reply_text(Messages.CHANGE_CURSE_FAILURE)
    except IndexError:
        await update.effective_message.reply_text(Messages.NOT_ENOUGH_ARGUMENTS)

reset_arguments = {
    "curse" : ("curse", "curse_percentage_messages", "curse_percentage_words"),
    "troll" : ("troll",),
    "shots" : ("shots",),
    "shot_at" : ("shot_at",),
    "message" : (),
    "word" : ()
}

@register_command(2, "Сбрасывает выбранный рейтинг от бота или метаданные чата")
@status_check
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tops_to_construct = reset_arguments.get(context.args[0], None)
        if tops_to_construct is None:
            await update.effective_message.reply_text(Messages.RESET_ACCIDENT)
            return

        for top_type in tops_to_construct:
            await update.effective_message.reply_text(
                construct_top(update.effective_chat.id, top_type, year_ago)
            )
        if context.args[0] == "shots":
            access_point.reset_shots(update.effective_chat.id)
        else:
            access_point.reset_event(
                update.effective_chat.id,
                context.args[0]
            )
        await update.effective_message.reply_text(Messages.RESET)
    except IndexError:
        await update.effective_message.reply_text(Messages.NOT_ENOUGH_ARGUMENTS)
        await update.effective_message.reply_text(Messages.RESET_ACCIDENT)

permit_arguments = {
    "random_send" : (
        1,
        "random_send_permit",
        "при включении бот будет со случайными промежутками от часа до 4 отправлять указанное сообщение"
    ),
    "troll" : (
        2,
        "trolling_permit",
        "при включении бот будет отмечать случайные сообщения реакцией 🤡"
    ),
    "regular_update" : (
        3,
        "regular_update_permit",
        "при включении бот будет регулярно (каждые 4 часа) отправлять отчеты по статистикам внутри сообщений"
    ),
    "high_noon" : (
        4,
        "high_noon_showdown_permit",
        "при включении бот реагирует на ответы внутри сообщения с командой /shoot"
    )
}

permit_help_message = construct_help(permit_arguments)

@register_command(2, "Изменяет разрешения бота. Введите -h для подробного набора аргументов.")
@argument_check(Messages.PERMIT_CHANGE_NOTHING)
@status_check
async def permit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.args[0] == "-h":
            await update.effective_message.reply_text(permit_help_message)
            return

        changed_permit = permit_arguments.get(context.args[0], None)
        if changed_permit is None:
            await update.effective_message.reply_text(Messages.INCORRECT_ARGUMENT)
            return

        changed, permit = access_point.change_status(
            update.effective_chat.id, changed_permit[1]
        )
        if changed:
            result = "Да" if permit == 1 else "Нет"
            await update.effective_message.reply_text(Messages.PERMIT_CHANGE_SUCCESS.format(context.args[0], result))
        else:
            await update.effective_message.reply_text(Messages.PERMIT_CHANGE_FAILURE.format(context.args[0]))
    except Exception as e:
        access_point.add_new_chat(update.effective_chat.id)
        await update.effective_message.reply_text(Messages.PERMIT_CHANGE_FAILURE.format(context.args[0]))

config_arguments = {
    "donation_link" : (
        1,
        "",
        DataType.DONATION_LINK,
        Messages.DONATE_CHANGE_SUCCESS,
        "отвечает за ссылку для доната"
    ),
    "random_send_message" : (
        2,
        "",
        DataType.RANDOM_SEND_MESSAGE,
        Messages.RANDOM_SEND_MESSAGE_SUCCESS,
        "отвечает за сообщение для случайной отправки"
    ),
    "curse_threshold" : (
        3,
        0,
        DataType.CURSE_THRESHOLD,
        Messages.CURSE_THRESHOLD_SUCCESS,
        "отвечает за порог количества мата, от которого бот отправит уведомление"
    ),
    "shoot_bot_easter_egg" : (
        4,
        "",
        DataType.SHOOT_BOT_EASTER_EGG,
        Messages.SHOOT_BOT_EASTER_EGG_MESSAGE_SUCCESS,
        "отвечает за сообщение-пасхалку в случае стрельбы в бота"
    )
}

config_help_message = construct_help(config_arguments)

@register_command(2, "Изменяет метаданные чата для бота. Введите -h для подробного набора аргументов.")
@argument_check(Messages.NOT_ENOUGH_ARGUMENTS)
@status_check
async def set_config_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.args[0] == "-h":
            await update.effective_message.reply_text(config_help_message)
            return

        entry = config_arguments.get(context.args[0], None)
        if entry is None:
            await update.effective_message.reply_text(Messages.INCORRECT_ARGUMENT)
            return

        _, arg_type, data_type, success = entry
        if isinstance(arg_type, str):
            new_data = " ".join(context.args[1:])
        elif isinstance(arg_type, int):
            new_data = int(context.args[1])
        else:
            raise Exception(f"Для данного типа не определены условия - {type(arg_type)}")

        access_point.update_data_from_main_table(
            [data_type],
            [DataType.CHAT_ID],
            new_data, update.effective_chat.id
        )

        await update.effective_message.reply_text(success)
    except Exception as e:
        access_point.add_new_chat(update.effective_chat.id)
        await update.effective_message.reply_text("Данные введены некорректно. Попробуйте ещё раз с другими данными.")