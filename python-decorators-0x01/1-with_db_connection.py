#!/usr/bin/python3
import sqlite3
import functools


def with_db_connection(func):
    """Decorator that opens an SQLite connection, passes it to the function,
    and ensures the connection is closed afterward."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            return func(conn, *args, **kwargs)
        finally:
            try:
                conn.close()
            except Exception:
                pass
    return wrapper


@with_db_connection
def get_user_by_id(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


# Fetch user by ID with automatic connection handling
user = get_user_by_id(user_id=1)
print(user)
