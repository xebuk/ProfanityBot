from enum import StrEnum

class Messages(StrEnum):
    I_SLEEP = "я пошел спать"

    I_AWAKE = "я проснулся"
    I_AWAKE_ALL_POLITE = "Либо речь чистая, либо чат тихий. Пойдет, в общем."
    I_AWAKE_ALL_TRAGEDY = "что-то вы тут матерились, давайте-ка оценим"

    ALERT = "ВНИМАНИЕ!\n"
    THANKS_FOR_ALERT = "Спасибо за внимание."

    CURSE_REACTION = "Ай-яй-яй, {}, плохие слова говоришь... Целых {}!"

    TOP_CURSE = "Список из ада:\n"
    TOP_CURSE_EVERYONE_IS_POLITE = "Пока все ангелочки)"

    TOP_TROLLING = "Список из клоунской: \n"
    TOP_TROLLING_NO_CLOWN = "Пока все хороши)"

    TOP_SHOTS = "Список из склепа: \n"
    TOP_SHOTS_EVERYONE_ARE_ALIVE = "Пока все живы)"

    REGULAR_TOP = "ВНИМАНИЕ! Отчет!"
    REGULAR_TOP_ALL_POLITE = "Пока никто ничего плохого не сказал... Хм..."
    REGULAR_TOP_ALL_TRAGEDY = "Ага, попались!"
    TOP_CURSE_REFRESH = "Список из ада (обновление на текущий момент): \n"
    REGULAR_TOP_SUCCESS = "Статус регулярного отчета по обсценной лексике для данного чата изменен на {}"
    REGULAR_TOP_FAILURE = "Статус регулярного отчета по обсценной лексике для данного чата не был изменен. Попробуйте ещё раз."

    TOP_ENTRY = "{}: {} - {}\n"
    TOP_RESULT = "Итого: {}"

    SHOOT_FAILURE = "Слот был не пустой..."
    SHOOT_SUCCESS = "Слот был пустой, вы выжили!"

    RESET = "Сброс данных произведен успешно."
    RESET_ACCIDENT = "Для предотвращения случайного сброса для работы команды надо ввести один из аргументов - curse или troll."

    CHANGE_CURSE_SUCCESS = "Рейтинг изменен успешно."
    CHANGE_CURSE_FAILURE = "Не удалось изменить рейтинг. Попробуйте позже."

    TROLL_SUCCESS = "Статус троллинга от бота для данного чата изменен на {}"
    TROLL_FAILURE = "Статус троллинга от бота для данного чата не был изменен. Попробуйте ещё раз."

    DONATE_CHANGE_NOTHING = "Вы не ввели ссылку для доната!"
    DONATE_CHANGE_SUCCESS = "Ссылка на донат изменена успешно!"

    RANDOM_SEND_LOGGING_SUCCESS = "Случайное сообщение было отправлено в {}"
    RANDOM_SEND_LOGGING_FAILURE = "Случайное сообщение не было отправлено в {}: {}"
    RANDOM_SEND_SUCCESS = "Статус случайной отправки в данный чат изменен на {}"
    RANDOM_SEND_FAILURE = "Статус случайной отправки в данный чат не был изменен. Попробуйте ещё раз."
    RANDOM_SEND_MESSAGE_NOTHING = "Вы не ввели сообщение для случайной отправки!"
    RANDOM_SEND_MESSAGE_SUCCESS = "Сообщение успешно изменено!"

    CURSE_THRESHOLD_NOTHING = "Вы не ввели подходящий аргумент!"
    CURSE_THRESHOLD_SUCCESS = "Порог уведомления изменен успешно!"
    CURSE_THRESHOLD_FAILURE = "Порог уведомления не был изменен. Попробуйте ещё раз."

    NOT_HIGH_ENOUGH_STATUS = "У вас недостаточно прав доступа в данном чате."
    PRIVATE_MESSAGES = "Данный бот не работает в личных сообщениях."
    UNREGISTERED_CHAT = "Данный чат не находится в зарегистрированных. Тыкните владельца бота для дальнейших действий."
    NOT_ENOUGH_ARGUMENTS = "Вы не ввели обязательные аргументы."

class SleepMessages(StrEnum):
    pass