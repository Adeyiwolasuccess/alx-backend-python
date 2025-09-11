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

# ---- cache_query (new decorator) ----
query_cache = {}
def cache_query(func):
    """Cache the results of the decorated function based on its query argument."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        query = kwargs.get("query")
        if query is None and args:
            query = args[0] if isinstance(args[0], str) else None
        if query in query_cache:
            print(f"[CACHE HIT] Returning cached results for query: {query}")
            return query_cache[query]
        result = func(*args, **kwargs)
        query_cache[query] = result
        return result
    return wrapper

@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")

#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")