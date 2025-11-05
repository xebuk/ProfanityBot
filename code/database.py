import sqlite3
import logging

def safe_chat_id(chat_id):
    if str(chat_id).isdigit():
        return chat_id
    else:
        return int("".join(c for c in str(chat_id) if c.isdigit()))

class DatabaseManager:
    def __init__(self, db_path="data/chats_with_curse.db"):
        self.db_path = db_path
        self.on_set_up()

    def on_set_up(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    create table if not exists chats (
                        chat_id integer primary key,
                        is_active integer not null default 1
                    )
                ''')

                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка инициализации таблицы чата: {e}")

    def add_new_chat(self, chat_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(
                    "select chat_id from chats where chat_id = ?",
                    (safe_chat,)
                )

                checked_id = cursor.fetchone()
                if checked_id is None:
                    cursor.execute(
                        "insert into chats (chat_id, is_active) values (?, ?)",
                        (safe_chat, 1)
                    )
                else:
                    cursor.execute(
                        "update chats set is_active = 1 where chat_id = ?",
                        (safe_chat,)
                    )
                conn.commit()

                cursor.execute(f'''
                    create table if not exists data_{safe_chat} (
                        user_id integer primary key,
                        user_name text not null,
                        curses integer default 0
                    )
                ''')
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка инициализации таблиц нового чата: {e}")

    def deactivate_chat(self, chat_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(
                    "update chats set is_active = 0 where chat_id = ?",
                    (safe_chat,)
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка установки чата как неактивного: {e}")

    def get_user_name(self, chat_id: int, user_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(f"select user_name from data_{safe_chat} where user_id = ?", (user_id,))
        except Exception as e:
            logging.error(f"Ошибка получения имени пользователя: {e}")
            self.add_new_chat(chat_id)
        finally:
            return cursor.fetchone()

    def get_user_names(self, chat_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(f"select user_name from data_{safe_chat}")
        except Exception as e:
            logging.error(f"Ошибка получения набора имен пользователей чата: {e}")
            self.add_new_chat(chat_id)
        finally:
            return cursor.fetchall()

    def get_user_curses(self, chat_id: int, user_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(f"select curses from data_{safe_chat} where user_id = ?", (user_id,))
        except Exception as e:
            logging.error(f"Ошибка получения счётчика матов пользователя: {e}")
            self.add_new_chat(chat_id)
        finally:
            return cursor.fetchone()

    def get_curses(self, chat_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(f"select user_id, user_name, curses from data_{safe_chat} order by curses desc")
        except Exception as e:
            logging.error(f"Ошибка при выгрузке данных о счетчиках мата: {e}")
            self.add_new_chat(chat_id)
        finally:
            return cursor.fetchall()

    def add_or_update_name(self, chat_id: int, user_id: int, new_name: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                user_name = self.get_user_name(chat_id, user_id)

                if user_name is None:
                    cursor.execute(
                        f"insert into data_{safe_chat} (user_id, user_name, curses) values (?, ?, ?)",
                        (user_id, new_name, 0)
                    )
                elif user_name[0] != new_name:
                    cursor.execute(
                        f"update data_{safe_chat} set user_name = ? where user_id = ?",
                        (new_name, user_id)
                    )
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка в изменении имени пользователя: {e}")
            self.add_new_chat(chat_id)

    def add_to_curses(self, chat_id: int, user_id: int, user_name: str, curses: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                old_curses = self.get_user_curses(chat_id, user_id)

                if old_curses is None:
                    cursor.execute(
                        f"insert into data_{safe_chat} (user_id, user_name, curses) values (?, ?, ?)",
                        (user_id, user_name, curses)
                    )
                else:
                    cursor.execute(
                        f"update data_{safe_chat} set curses = ? where user_id = ?",
                        (old_curses[0] + curses, user_id)
                    )
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка при увеличении счётчика мата: {e}")
            self.add_new_chat(chat_id)

    def reset_chat(self, chat_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(f"update data_{safe_chat} set curses = 0")
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка при попытке сброса состояния чата: {e}")
            self.add_new_chat(chat_id)

    def hard_reset_chat(self, chat_id: int):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                safe_chat = safe_chat_id(chat_id)

                cursor.execute(f"delete from data_{safe_chat}")
                conn.commit()
        except Exception as e:
            logging.error(f"Ошибка при попытке полного сброса состояния чата: {e}")
            self.add_new_chat(chat_id)
