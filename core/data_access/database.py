import sqlite3
import enum
from typing import Any
from atexit import register

from core.data_access.logs import database_log

def safe_chat_id(chat_id):
    if isinstance(chat_id, int):
        return abs(chat_id)
    else:
        return int("".join(c for c in str(chat_id) if c.isdigit()))

class DataType(enum.Enum):
    INSIDE_ID = ("chats", int, "inside_id")                                       # - число
    CHAT_ID = ("chats", int, "chat_id")                                           # - число
    IS_ACTIVE = ("chats", int, "is_active")                                       # - 0 или 1
    PRIVACY = ("chats", int, "privacy")                                           # - 0 или 1
    CHAT_NAME = ("chats", str, "chat_name")                                       # - текст
    DONATION_LINK = ("chats", str, "donation_link")                               # - текст
    IS_PERMITTED_TO_RANDOM_SEND = ("chats", int, "is_permitted_to_random_send")   # - 0 или 1
    RANDOM_SEND_MESSAGE = ("chats", str, "random_send_message")                   # - текст
    CAN_BE_TROLLED = ("chats", int, "can_be_trolled")                             # - 0 или 1

    USER_ID = ("data", int, "user_id")                                            # - число
    USER_NAME = ("data", str, "user_name")                                        # - текст
    CURSES = ("data", int, "curses")                                              # - число
    TROLLS = ("data", int, "trolls")                                              # - число

    @property
    def table(self):
        return self.value[0]

    @property
    def type(self):
        return self.value[1]

    @property
    def cell(self):
        return self.value[2]

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
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()
        except Exception as e:
            database_log.error(f"Ошибка инициализации базы данных - {e}")
            raise e
        try:
            self.cursor.execute("""
                create table if not exists chats (
                    inside_id integer not null unique primary key,
                	chat_id	integer not null unique primary key,
                	is_active integer not null default 1,
                	privacy integer not null default 1,
                	chat_name text default 'stub',
                	donation_link text default 'stub',
                	is_permitted_to_random_send	integer not null default 0,
                	random_send_message text not null default 'stub',
                	can_be_trolled integer not null default 0
                )
            """)
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка инициализации таблицы чата: {e}")
            raise e

    def shutdown(self):
        self.cursor.close()
        self.conn.close()

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
                    "insert into chats (chat_id, privacy, is_active, is_permitted_to_random_send) values (?, ?, ?, ?)",
                    (chat_id, 1, 1, 0)
                )
                self.conn.commit()

                inside_id = self.get_chat(chat_id)
                self.cursor.execute(f"""
                    create table if not exists data_{inside_id} (
                        user_id integer unique primary key,
                        user_name text not null default 'stub',
                        curses integer not null default 0,
                        trolls integer not null default 0
                    )
                """)
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
                "insert into chats (chat_id, is_active) values (?, ?)",
                (chat_id, 0)
            )
            self.conn.commit()

    def reset_chat(self, chat_id: int):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(f"update data_{inside_id} set curses = 0")
            self.cursor.execute(f"update data_{inside_id} set trolls = 0")
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

    def change_curses_userid(self, chat_id: int, user_id: int, curses: int, user_name: str | None):
        try:
            inside_id = self.get_chat(chat_id)

            if user_name is None:
                self.cursor.execute(f"""
                    insert into data_{inside_id} (user_id, curses) values (?, ?)
                    on conflict (user_id) do update set curses = curses + ?
                """, (user_id, curses, curses))
            else:
                self.cursor.execute(f"""
                    insert into data_{inside_id} (user_id, user_name, curses) values (?, ?, ?)
                    on conflict (user_id) do update set curses = curses + ?, user_name = ?
                """, (user_id, user_name, curses, curses, user_name))

            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка при увеличении счётчика мата через user_id: {e}")
            self.add_new_chat(chat_id)

    def change_curses_username(self, chat_id: int, user_name: str, curses: int):
        try:
            inside_id = self.get_chat(chat_id)
            self.cursor.execute(
                f"update data_{inside_id} set curses = curses + ? where user_name = ?",
                (curses, user_name)
            )

            self.conn.commit()
            return True
        except Exception as e:
            database_log.error(f"Ошибка при увеличении счётчика мата: {e}")
            self.add_new_chat(chat_id)
            return False

    def change_trolls(self, chat_id: int, user_id: int, user_name: str | None):
        try:
            inside_id = self.get_chat(chat_id)

            if user_name is None:
                self.cursor.execute(f"""
                    insert into data_{inside_id} (user_id, trolls) values (?, 1)
                    on conflict (user_id) do update set trolls = trolls + 1
                """, (user_id,))
            else:
                self.cursor.execute(f"""
                    insert into data_{inside_id} (user_id, user_name, trolls) values (?, ?, 1)
                    on conflict (user_id) do update set trolls = trolls + 1, user_name = ?
                """, (user_id, user_name, user_name))

            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка при увеличении счётчика мата через user_id: {e}")
            self.add_new_chat(chat_id)

    def change_random_send_status(self, chat_id: int):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(
                "update chats set is_permitted_to_random_send = not is_permitted_to_random_send where inside_id = ? returning is_permitted_to_random_send",
                (inside_id,)
            )
            permit = self.cursor.fetchone()[0] == 1

            self.conn.commit()
            return True, permit
        except Exception as e:
            database_log.error(f"Ошибка при попытке изменения статуса случайной отправки для чата: {e}")
            self.add_new_chat(chat_id)
            return False, 0

    def change_trolling_status(self, chat_id: int):
        try:
            inside_id = self.get_chat(chat_id)

            self.cursor.execute(
                "update chats set can_be_trolled = not can_be_trolled where inside_id = ? returning can_be_trolled",
                (inside_id,)
            )
            permit = self.cursor.fetchone()[0] == 1

            self.conn.commit()
            return True, permit
        except Exception as e:
            database_log.error(f"Ошибка при попытке изменения статуса троллинга для чата: {e}")
            self.add_new_chat(chat_id)
            return False, 0

access_point = DatabaseManager()
register(access_point.shutdown)