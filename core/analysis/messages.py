from enum import StrEnum

class Messages(StrEnum):
    I_SLEEP = "я пошел спать"
    I_AWAKE = "я проснулся"

    ALERT = "ВНИМАНИЕ! \n"
    THANKS_FOR_ALERT = "Спасибо за внимание."

    GOOD_AWAKENING = "Всем доброе утро (день, вечер, ночь)! \n"
    GOOD_SLEEP = "Всем спокойных снов! \n"
    NOT_GOOD_SLEEP = "У меня тут проблема, так что пока не спокойной ночи, но сча разберусь."

    CURSE_REACTION = "Ай-яй-яй, {}, плохие слова говоришь... Целых {}!"

    TOP_CURSE = "Список из ада:\n"
    TOP_CURSE_EVERYONE_IS_POLITE = "Пока все ангелочки)"

    TOP_CURSE_MESSAGES = "Список из ада (отношение к сообщениям): \n"
    TOP_CURSE_WORDS = "Список из ада (отношение к словам): \n"

    TOP_CURSE_REFRESH = "Список из ада (последние 2 часа): \n"
    TOP_CURSE_REFRESH_EVERYONE_IS_POLITE = "Пока никто ничего плохого не сказал... Хм..."
    TOP_CURSE_REFRESH_TRAGEDY = "Ага, попались! В банке монетки появились! \n"

    TOP_TROLLING = "Список из клоунской: \n"
    TOP_TROLLING_NO_CLOWN = "Пока все хороши)"

    TOP_TROLLING_REFRESH = "Список из клоунской (последние 2 часа): \n"
    TOP_TROLLING_REFRESH_NO_CLOWN = "Клоунский костюм висит пыльный, его пока никто не носил. Странно..."
    TOP_TROLLING_REFRESH_TRAGEDY = "Ага, попались! Парика не вижу! \n"

    TOP_SHOTS = "Список из склепа: \n"
    TOP_SHOTS_EVERYONE_ARE_ALIVE = "Пока все живы)"

    TOP_SHOT = "Список из медпункта: \n"
    TOP_SHOT_NO_BLOOD = "Пока никого не подстрелили)"

    TOP_SHOT_REFRESH = "Список из медпункта (последние 2 часа): \n"
    TOP_SHOT_REFRESH_CLEAR_GAUZE = "Бинты остались в упаковке. Хорошо..."
    TOP_SHOT_REFRESH_TRAGEDY = "Ага, попались! Упаковка бинтов пропала! \n"

    TOP_INSOMNIA = "Список от ночника: \n"
    TOP_INSOMNIA_EVERYONE_ASLEEP = "Пока все спят)"

    REGULAR_TOP = "ВНИМАНИЕ! Отчет!"
    REGULAR_TOP_SUCCESS = "Статус регулярного отчета по обсценной лексике для данного чата изменен на {}"
    REGULAR_TOP_FAILURE = "Статус регулярного отчета по обсценной лексике для данного чата не был изменен. Попробуйте ещё раз."

    REGULAR_BULLET_REFRESH = "Пули пополнены!"

    TOP_ENTRY = "{}: {} - {}\n"
    TOP_RESULT = "Итого: {}"

    SHOOT_FAILURE = "Слот был не пустой..."
    SHOOT_SUCCESS = "Слот был пустой, вы выжили!"

    RESET = "Сброс данных произведен успешно."
    RESET_ACCIDENT = "Для предотвращения случайного сброса для работы команды надо ввести один из аргументов - curse, troll, shots, shot_at, word или message."

    CHANGE_CURSE_SUCCESS = "Рейтинг изменен успешно."
    CHANGE_CURSE_FAILURE = "Не удалось изменить рейтинг. Попробуйте позже."

    PERMIT_CHANGE_SUCCESS = "Статус {} изменен на {}"
    PERMIT_CHANGE_FAILURE = "Статус {} не был изменен. Попробуйте ещё раз."
    PERMIT_CHANGE_NOTHING = "Вы не ввели разрешение, которое нужно изменить!"

    TROLL_SUCCESS = "Статус троллинга от бота для данного чата изменен на {}"
    TROLL_FAILURE = "Статус троллинга от бота для данного чата не был изменен. Попробуйте ещё раз."

    RANDOM_SEND_LOGGING_SUCCESS = "Случайное сообщение было отправлено в {}"
    RANDOM_SEND_LOGGING_FAILURE = "Случайное сообщение не было отправлено в {}: {}"
    RANDOM_SEND_SUCCESS = "Статус случайной отправки в данный чат изменен на {}"
    RANDOM_SEND_FAILURE = "Статус случайной отправки в данный чат не был изменен. Попробуйте ещё раз."

    DONATE_CHANGE_SUCCESS = "Ссылка на донат изменена успешно!"
    RANDOM_SEND_MESSAGE_SUCCESS = "Сообщение успешно изменено!"
    SHOOT_BOT_EASTER_EGG_MESSAGE_SUCCESS = "Сообщение-пасхалка успешно изменена!"
    CURSE_THRESHOLD_SUCCESS = "Порог уведомления изменен успешно!"

    NOT_HIGH_ENOUGH_STATUS = "У вас недостаточно прав доступа в данном чате."
    PRIVATE_MESSAGES = "Данный бот не работает в личных сообщениях."
    UNREGISTERED_CHAT = "Данный чат не находится в зарегистрированных. Тыкните владельца бота для дальнейших действий."
    NOT_ENOUGH_ARGUMENTS = "Вы не ввели обязательные аргументы."
    INCORRECT_ARGUMENT = "Вы ввели некорректный аргумент. Попробуйте ещё раз с другим аргументом или введите -h для списка возможных аргументов."

class SleepMessages(StrEnum):
    pass