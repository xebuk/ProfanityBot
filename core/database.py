import sqlite3
import enum
from typing import Any

from logs import database_log

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

    USER_ID = ("data", int, "user_id")                                            # - число
    USER_NAME = ("data", str, "user_name")                                        # - текст
    CURSES = ("data", int, "curses")                                              # - число

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
        what: list[DataType]
):
    vals = ", ".join(w.cell for w in what)
    placeholders = ", ".join(["?"] * len(what))
    sql_query = f"insert into {table} ({vals}) values ({placeholders})"

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
            self.cursor.execute('''
                create table if not exists chats (
                    inside_id integer primary key,
                	chat_id	integer primary key,
                	is_active integer not null default 1,
                	privacy integer not null default 1,
                	chat_name text default 'stub',
                	donation_link text default 'stub',
                	is_permitted_to_random_send	integer not null default 0,
                	random_send_message text not null default 'stub'
                )
            ''')
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
                    "insert into chats (chat_id, is_privated, is_active, is_permitted_to_random_send) values (?, ?, ?, ?)",
                    (chat_id, 1, 1, 0)
                )
                self.conn.commit()

                inside_id = self.get_chat(chat_id)
                self.cursor.execute(f'''
                    create table if not exists data_{inside_id} (
                        user_id integer primary key,
                        user_name text not null default 'stub',
                        curses integer default 0
                    )
                ''')
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

    def add_or_update_name(self, chat_id: int, user_id: int, new_name: str):
        try:
            inside_id = self.get_chat(chat_id)
            user_name = self.get_data_from_chat(
                chat_id,
                [DataType.USER_NAME],
                [DataType.USER_ID],
                None,
                False, True,
                user_id
            )

            if user_name is None:
                self.cursor.execute(
                    f"insert into data_{inside_id} (user_id, user_name, curses) values (?, ?, ?)",
                    (user_id, new_name, 0)
                )
            elif user_name[0] != new_name:
                self.cursor.execute(
                    f"update data_{inside_id} set user_name = ? where user_id = ?",
                    (new_name, user_id)
                )

            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка в изменении имени пользователя: {e}")
            self.add_new_chat(chat_id)

    def change_curses_userid(self, chat_id: int, user_id: int, curses: int, user_name: str | None):
        try:
            inside_id = self.get_chat(chat_id)

            old_curses = self.get_data_from_chat(
                chat_id,
                [DataType.CURSES],
                [DataType.USER_ID],
                None,
                False, True,
                user_id
            )[0]

            if old_curses is None:
                if user_name is None:
                    self.cursor.execute(
                        f"insert into data_{inside_id} (user_id, curses) values (?, ?)",
                        (user_id, curses)
                    )
                else:
                    self.cursor.execute(
                        f"insert into data_{inside_id} (user_id, user_name, curses) values (?, ?, ?)",
                        (user_id, user_name, curses)
                    )
            else:
                self.cursor.execute(
                    f"update data_{inside_id} set curses = ? where user_id = ?",
                    (old_curses + curses, user_id)
                )
            self.conn.commit()
        except Exception as e:
            database_log.error(f"Ошибка при увеличении счётчика мата через user_id: {e}")
            self.add_new_chat(chat_id)

    def change_curses_username(self, chat_id: int, user_name: str, curses: int):
        try:
            inside_id = self.get_chat(chat_id)

            old_curses = self.get_data_from_chat(
                chat_id,
                [DataType.CURSES],
                [DataType.USER_NAME],
                None,
                False, True,
                user_name
            )[0]

            if old_curses is not None:
                self.cursor.execute(
                    f"update data_{inside_id} set curses = ? where user_name = ?",
                    (old_curses + curses, user_name)
                )
            else:
                database_log.error(f"Не удалось увеличить счетчик мата для {user_name}")
                return False
            self.conn.commit()
            return True
        except Exception as e:
            database_log.error(f"Ошибка при увеличении счётчика мата: {e}")
            self.add_new_chat(chat_id)
            return False

    def change_random_send_status(self, chat_id: int):
        try:
            inside_id = self.get_chat(chat_id)
            self.cursor.execute(
                "select is_permitted_to_random_send from chats where inside_id = ?",
                (inside_id,)
            )
            permit = self.cursor.fetchone()[0] == 1

            self.cursor.execute(
                "update chats set is_permitted_to_random_send = ? where inside_id = ?",
                (1 if not permit else 0, inside_id)
            )
            self.conn.commit()
            return True, not permit
        except Exception as e:
            database_log.error(f"Ошибка при попытке изменения статуса случайной отправки для чата: {e}")
            self.add_new_chat(chat_id)
            return False, 0