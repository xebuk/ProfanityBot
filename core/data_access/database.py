import datetime
from sqlite3 import connect
from enum import Enum
from typing import Any, LiteralString

from .logs import database_log

class DataType(Enum):
    INSIDE_ID = ("chats", int, "inside_id", "nu", 0)                                                       # - число
    CHAT_ID = ("chats", int, "chat_id", "nu", 0)                                                           # - число
    IS_ACTIVE = ("chats", int, "is_active", "nd", 1)                                                       # - 0 или 1
    PRIVACY = ("chats", int, "privacy", "nd", 1)                                                           # - 0 или 1
    QUIET_MODE = ("chats", int, "quiet_mode", "nd", 1)                                                     # - 0 или 1

    CHAT_NAME = ("chats", str, "chat_name", "nd", "stub")                                                  # - текст

    RANDOM_SEND_PERMIT = ("chats", int, "random_send_permit", "nd", 0)                                     # - 0 или 1
    TROLLING_PERMIT = ("chats", int, "trolling_permit", "nd", 0)                                           # - 0 или 1
    REGULAR_UPDATE_PERMIT = ("chats", int, "regular_update_permit", "nd", 0)                               # - 0 или 1
    HIGH_NOON_SHOWDOWN_PERMIT = ("chats", int, "high_noon_showdown_permit", "nd", 0)                       # - 0 или 1
    QUIET_NIGHT_MODE = ("chats", int, "quiet_night_mode", "nd", 0)                                         # - 0 или 1

    DONATION_LINK = ("chats", str, "donation_link", "nd", "stub")                                          # - текст
    CURSE_THRESHOLD = ("chats", int, "curse_threshold", "nd", 2)                                           # - число
    RANDOM_SEND_MESSAGE = ("chats", str, "random_send_message", "nd", "stub")                              # - текст
    SLEEP_START_TIME = ("chats", str, "sleep_start_time", "nd", "stub")                                    # - текст (время)
    SHOOT_BOT_EASTER_EGG = ("chats", str, "shoot_bot_easter_egg", "nd", "stub")                            # - текст


    USER_ID = ("data_number_pattern", int, "user_id", "nu", 0)                                             # - число
    USER_NAME = ("data_number_pattern", str, "user_name", "nd", "stub")                                    # - текст
    CURRENT_SHOTS = ("data_number_pattern", int, "current_shots", "nd", 0)                                 # - число
    BULLET_POSSESSION = ("data_number_pattern", int, "bullet_possession", "nd", 0)                         # - 0 или 1


    EVENT_TIME = ("log_book_number_pattern", str, "event_time", "n", "stub")                               # - текст (время)
    USER_ID_EVENT = ("log_book_number_pattern", int, "user_id", "n", 0)                                    # - число
    EVENT_TYPE = ("log_book_number_pattern", str, "event_type", "n", "stub")                               # - текст
    AMOUNT = ("log_book_number_pattern", int, "amount", "n", 0)                                            # - число

    @property
    def table(self):
        return self.value[0]

    @property
    def type(self):
        return self.value[1]

    @property
    def cell(self):
        return self.value[2]

    @property
    def modifiers(self):
        return self.value[3]

    @property
    def default(self):
        return self.value[4]

type_mapping = {
    int: "integer",
    str: "text",
    float: "real",
    bytes: "blob"
}

def construct_table(table: str) -> str:
    table_list: list[tuple[str, str, str]] = list()

    for item in DataType:
        table_name, data_type, column_name, parameters, default_value = item.value

        if table_name != table:
            continue

        sql_type = type_mapping.get(data_type, "text")
        auxiliary_parameters = list()

        if parameters.find("n") != -1:
            auxiliary_parameters.append("not null")

        if parameters.find("u") != -1:
            auxiliary_parameters.append("unique")

        if parameters.find("d") != -1:
            if isinstance(default_value, str):
                formatted_default = f"'{default_value}'"
            else:
                formatted_default = str(default_value)

            auxiliary_parameters.append(f"default {formatted_default}")

        table_list.append((column_name, sql_type, " ".join(auxiliary_parameters)))

    column_definitions = []
    for column in table_list:
        col_name, sql_type, default_val = column
        column_definitions.append(
            f"    {col_name} {sql_type} {default_val}"
        )

    column_sql = ",\n".join(column_definitions)
    query = f"""create table if not exists {table} (
{column_sql}
)"""
    return query

def construct_select(
        table: str,
        what: list[DataType] | None,
        where: list[DataType] | None,
        order_by: list[DataType] | None,
        order_by_desc: bool | None
):
    select_part = ", ".join(w.cell for w in what) if what is not None and what else "*"
    sql_query = f"select {select_part} from {table}"

    if where is not None and where:
        where_part = " and ".join(f"{w.cell} = ?" for w in where)
        sql_query += f" where {where_part}"
    if order_by is not None and order_by:
        order_by_part = ", ".join(o.cell for o in order_by)
        sql_query += f" order by {order_by_part}"
        if order_by_desc is not None and order_by_desc:
            sql_query += " desc"
        else:
            sql_query += " asc"

    return sql_query

def construct_insert(
        table: str,
        what: list[DataType],
        replace: bool | None
):
    vals = ", ".join(w.cell for w in what)
    placeholders = ", ".join(["?"] * len(what))
    replace_clause = "" if replace is None or not replace else " or replace "
    sql_query = f"insert{replace_clause} into {table} ({vals}) values ({placeholders})"

    return sql_query

def construct_update(
        table: str,
        what: list[DataType],
        where: list[DataType] | None
):
    set_part = ', '.join(f"{w.cell} = ?" for w in what)
    sql_query = f"update {table} set {set_part}"
    if where is not None:
        where_part = " and ".join(f"{w.cell} = ?" for w in where)
        sql_query += f" where {where_part}"

    return sql_query

class DatabaseManager:
    def __init__(self, db_path="./data/chats_with_curse.db"):
        self.db_path = db_path
        try:
            self.conn = connect(db_path)
            self.cursor = self.conn.cursor()
        except Exception as e:
            database_log.error(f"Ошибка инициализации базы данных - {e}")
            raise e
        try:
            self.cursor.execute(construct_table("chats"))
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка инициализации таблицы чата: {e}")
            raise e

    def shutdown(self):
        database_log.info("Запустил функцию выхода")
        self.cursor.close()
        self.conn.commit()
        self.conn.close()
        database_log.info("Завершил выполнение инструкций при выходе")

    def get_chat(self, chat_id: int):
        self.cursor.execute("select inside_id from chats where chat_id = ?",(chat_id,))
        return self.cursor.fetchone()[0]

    def add_new_chat(self, chat_id: int):
        try:
            self.cursor.execute(
                "select chat_id from chats where chat_id = ?",
                (chat_id,)
            )
            checked_id = self.cursor.fetchone()
            if checked_id is None:
                self.cursor.execute(
                    "insert into chats (chat_id) values (?)",
                    (chat_id,)
                )
                self.conn.commit()

                inside_id = self.get_chat(chat_id)
                self.cursor.execute(
                    construct_table("data_number_pattern")
                    .replace("number_pattern", str(inside_id))
                )
                self.cursor.execute(
                    construct_table("log_book_number_pattern")
                    .replace("number_pattern", str(inside_id))
                )
            else:
                self.cursor.execute(
                    "update chats set is_active = 1 where chat_id = ?",
                    (chat_id,)
                )
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка инициализации таблиц нового чата: {e}")
            raise e

    def deactivate_chat(self, chat_id: int):
        try:
            self.cursor.execute(
                "update chats set is_active = 0 where chat_id = ?",
                (chat_id,)
            )
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка установки чата как неактивного: {e}")
            self.cursor.execute(
                "insert into chats (chat_id) values (?)",
                (chat_id,)
            )
            self.conn.commit()

    def reset_chat(self, chat_id: int, what: LiteralString):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(f"update data_{inside_id} set {what} = 0")
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка при попытке сброса состояния чата: {e}")
            self.add_new_chat(chat_id)

    def hard_reset_chat(self, chat_id: int):
        try:
            inside_id = self.get_chat(chat_id)
            self.cursor.execute(f"delete from data_{inside_id}")
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка при попытке полного сброса состояния чата: {e}")
            self.add_new_chat(chat_id)

    def get_data_from_chat(
            self,
            chat_id: int,
            what: list[DataType] | None,
            where: list[DataType] | None,
            order_by: list[DataType] | None,
            order_by_desc: bool | None,
            fetchone: bool | None,
            *args: Any
    ):
        inside_id = self.get_chat(chat_id)
        sql_query = construct_select(f"data_{inside_id}", what, where, order_by, order_by_desc)
        try:
            self.cursor.execute(sql_query, args)
        except Exception as e:
            database_log.error(f"Ошибка получения данных от таблицы чата: {sql_query} - {args} - {e}")
            self.add_new_chat(chat_id)
        finally:
            if fetchone is None or not fetchone:
                return self.cursor.fetchall()
            return self.cursor.fetchone()

    def get_data_from_main_table(
            self,
            what: list[DataType] | None,
            where: list[DataType] | None,
            order_by: DataType | None,
            order_by_desc: bool | None,
            fetchone: bool | None,
            *args: Any
    ):
        sql_query = construct_select("chats", what, where, order_by, order_by_desc)
        try:
            self.cursor.execute(sql_query, args)
        except Exception as e:
            database_log.error(f"Ошибка получения данных от главной таблицы: {sql_query} - {args} - {e}")
        finally:
            if fetchone is None or not fetchone:
                return self.cursor.fetchall()
            return self.cursor.fetchone()

    def get_data_from_queue(
            self,
            what: list[DataType] | None,
            fetchone: bool | None
    ):
        sql_query = construct_select("on_queue", what, None, None, None)
        try:
            self.cursor.execute(sql_query)
        except Exception as e:
            database_log.error(f"Ошибка получения данных от таблицы очереди: {sql_query} - {e}")
        finally:
            if fetchone is None or not fetchone:
                return self.cursor.fetchall()
            return self.cursor.fetchone()

    def update_data_from_chat(
            self,
            chat_id: int,
            what: list[DataType] | None,
            where: list[DataType] | None,
            *args: Any
    ):
        inside_id = self.get_chat(chat_id)
        sql_query = construct_update(f"data_{inside_id}", what, where)
        try:
            self.cursor.execute(sql_query, args)
        except Exception as e:
            database_log.error(f"Ошибка изменения данных в таблице чата: {sql_query} - {args} - {e}")
            self.conn.rollback()
            self.add_new_chat(chat_id)

        self.conn.commit()

    def update_data_from_main_table(
            self,
            what: list[DataType] | None,
            where: list[DataType] | None,
            *args: Any
    ):
        sql_query = construct_update("chats", what, where)
        try:
            self.cursor.execute(sql_query, args)
        except Exception as e:
            database_log.error(f"Ошибка изменения данных в таблице чата: {sql_query} - {args} - {e}")
            self.conn.rollback()

        self.conn.commit()

    def insert_data_into_queue(self, chat_id: int, chat_name: str):
        sql_query = construct_insert("on_queue", [DataType.CHAT_ID, DataType.CHAT_NAME], True)
        try:
            self.cursor.execute(sql_query, (chat_id, chat_name))
        except Exception as e:
            database_log.error(f"Ошибка добавления данных в таблицу очереди: {e}")
            self.conn.rollback()

        self.conn.commit()

    def get_users(self, chat_id: int):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(f"""
                select user_id from data_{inside_id}
            """)

            return self.cursor.fetchall()
        except Exception as e:
            database_log.error(f"Ошибка при получении данных о пользователях: {e}")

    def register_event(self, chat_id: int, user_id: int, event_type: str, amount: int):
        current_time = datetime.datetime.now().isoformat(
            sep=' ',
            timespec='microseconds'
        )

        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(f"""
                insert into log_book_{inside_id} (event_time, user_id, event_type, amount)
                values (?, ?, ?, ?)
            """, (current_time, user_id, event_type, amount))

            self.conn.commit()
            return True
        except Exception as e:
            database_log.error(f"Ошибка при регистрации ивента: {e}")
            return False

    def pull_chat_wide_event(self, chat_id: int, command: str, delta: datetime.timedelta):
        from_when = (datetime.datetime.now() - delta).isoformat(
            sep=' ',
            timespec='microseconds'
        )

        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(f"""
                select lb.user_id, d.user_name, lb.event_type, {command}(lb.amount) from log_book_{inside_id} lb
                join data_{inside_id} d on d.user_id = lb.user_id
                where lb.event_time >= ?
                group by lb.user_id, d.user_name, lb.event_type
            """, (from_when,))

            return self.cursor.fetchall()
        except Exception as e:
            database_log.error(f"Ошибка при выборке ивентов по всему чату: {e}")

    def add_or_update_name(self, chat_id: int, user_id: int, new_name: str):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(f"""
                insert into data_{inside_id} (user_id, user_name) values (?, ?)
                on conflict (user_id) do update set user_name = ?
            """, (user_id, new_name, new_name))

            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка в изменении имени пользователя: {e}")
            self.add_new_chat(chat_id)

    def change_curses_username(self, chat_id: int, user_name: str, curses: int):
        try:
            inside_id = self.get_chat(chat_id)
            self.cursor.execute(
                f"update data_{inside_id} set curses = curses + ?, word_counter_curses = word_counter_curses + ? where user_name = ?",
                (curses, curses, user_name)
            )

            self.conn.commit()
            return True
        except Exception as e:
            database_log.error(f"Ошибка при изменении счётчика мата через user_name: {e}")
            self.add_new_chat(chat_id)
            return False

    def reset_event(self, chat_id: int, event_type: str):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(f"""
                delete from data_{inside_id} where event_type = ?
            """, (event_type,))

            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка при попытке очистки ивента типа {event_type}: {e}")
            self.add_new_chat(chat_id)

    def reset_shots(self, chat_id: int):
        try:
            inside_id = self.get_chat(chat_id)
            self.cursor.execute(f"update data_{inside_id} set current_shots = 0")
            self.cursor.execute(f"""
                delete from data_{inside_id} where event_type = N'shot_fail'
            """)
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка при сбросе счетчика стрельбы: {e}")
            self.add_new_chat(chat_id)

    def change_status(self, chat_id: int, what_permit: str):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(
                f"update chats set {what_permit} = not {what_permit} where inside_id = ? returning {what_permit}",
                (inside_id,)
            )
            permit = self.cursor.fetchone()[0]

            self.conn.commit()
            return True, permit
        except Exception as e:
            database_log.error(f"Ошибка при попытке изменения статуса разрешения типа {what_permit}: {e}")
            self.add_new_chat(chat_id)
            return False, 0

access_point = DatabaseManager()