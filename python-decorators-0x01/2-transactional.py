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

def transactional(func):
    """Wrap a DB operation in a transaction: COMMIT on success, ROLLBACK on error."""
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            result = func(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            try:
                conn.rollback()
            finally:
                # Re-raise the original error after rollback so callers see it
                raise
    return wrapper

@with_db_connection 
@transactional 
def update_user_email(conn, user_id, new_email): 
    cursor = conn.cursor() 
    cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id)) 
    #### Update user's email with automatic transaction handling 

update_user_email(user_id=1, new_email='Crawford_Cartwright@hotmail.com')