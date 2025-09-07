#!/usr/bin/python3
"""
0-stream_users.py

Defines stream_users() — a generator that yields rows one by one
from the user_data table in ALX_prodev database.
"""

import os
import mysql.connector
from typing import Dict, Generator, Optional


def stream_users() -> Generator[Dict[str, object], None, None]:
    """
    Generator that streams rows from user_data table one by one.
    Uses a single loop with `yield`.
    """
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD")
    port = int(os.getenv("MYSQL_PORT", "3306"))

    conn: Optional[mysql.connector.MySQLConnection] = None
    cur = None

    try:
        conn = mysql.connector.connect(
            host=host, user=user, password=password, port=port, database="ALX_prodev"
        )
        cur = conn.cursor(dictionary=True)

        cur.execute("SELECT user_id, name, email, age FROM user_data ORDER BY name;")

        # ONE loop only
        for row in cur:
            # convert DECIMAL age to int if possible
            if row.get("age") is not None:
                try:
                    row["age"] = int(row["age"])
                except Exception:
                    pass
            yield row

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == "__main__":
    # Demo: print first 5 rows
    for i, row in enumerate(stream_users()):
        print(row)
        if i == 4:
            break
