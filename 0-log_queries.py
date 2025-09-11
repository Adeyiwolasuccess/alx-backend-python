#!/usr/bin/python3
import sqlite3
import functools

# decorator to log SQL queries
def log_queries(func):
    """Decorator that logs the SQL query before executing the wrapped function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        query = kwargs.get("query")
        if query is None and args:
            query = args[0] if isinstance(args[0], str) else None
        print(f"[SQL] {query if query is not None else 'UNKNOWN QUERY'}")
        return func(*args, **kwargs)
    return wrapper

@log_queries
def fetch_all_users(query):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

#### fetch users while logging the query
users = fetch_all_users(query="SELECT * FROM users")