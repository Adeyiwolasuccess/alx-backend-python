#!/usr/bin/python3
import time
import sqlite3
import functools

# ---- with_db_connection (from previous task) ----
def with_db_connection(func):
    """Open an SQLite connection, pass it as first arg `conn`, and close it after."""
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

# ---- retry_on_failure (new decorator) ----
def retry_on_failure(retries=3, delay=2):
    """Retry the decorated function up to `retries` times with `delay` seconds between."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= retries:
                        raise
                    print(f"Attempt {attempts} failed: {e}. Retrying in {delay} seconds...")
                    time.sleep(delay)
        return wrapper
    return decorator

@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


# ---- attempt to fetch users with automatic retry on failure ----
if __name__ == "__main__":
    users = fetch_users_with_retry()
    print(users)