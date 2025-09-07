#!/usr/bin/python3
"""
seed.py — Setup ALX_prodev.user_data and load CSV, plus a row-streaming generator.

Prototypes satisfied:
- connect_db()
- create_database(connection)
- connect_to_prodev()
- create_table(connection)
- insert_data(connection, data)  # here, 'data' is a CSV filepath string

Extra (for the objective): stream_users(connection, batch_size=500)
"""

import csv
import os
import uuid
from typing import Dict, Generator, Iterable, Optional

import mysql.connector
from mysql.connector import MySQLConnection


# --------- Prototype 1 ----------
def connect_db() -> Optional[MySQLConnection]:
    """connects to the mysql database server (no specific database)"""
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", None)
    port = int(os.getenv("MYSQL_PORT", "3306"))
    try:
        conn = mysql.connector.connect(
            host=host, user=user, password=password, port=port
        )
        return conn
    except mysql.connector.Error as e:
        print(f"[MySQL Error] connect_db: {e}")
        return None


# --------- Prototype 2 ----------
def create_database(connection: MySQLConnection) -> None:
    """creates the database ALX_prodev if it does not exist"""
    with connection.cursor() as cur:
        cur.execute(
            "CREATE DATABASE IF NOT EXISTS ALX_prodev "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
    connection.commit()


# --------- Prototype 3 ----------
def connect_to_prodev() -> Optional[MySQLConnection]:
    """connects the the ALX_prodev database in MYSQL"""
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", None)
    port = int(os.getenv("MYSQL_PORT", "3306"))
    try:
        conn = mysql.connector.connect(
            host=host, user=user, password=password, port=port, database="ALX_prodev"
        )
        return conn
    except mysql.connector.Error as e:
        print(f"[MySQL Error] connect_to_prodev: {e}")
        return None


# --------- Prototype 4 ----------
def create_table(connection: MySQLConnection) -> None:
    """creates a table user_data if it does not exists with the required fields"""
    ddl = """
    CREATE TABLE IF NOT EXISTS user_data (
        user_id CHAR(36) NOT NULL PRIMARY KEY,
        name    VARCHAR(255) NOT NULL,
        email   VARCHAR(255) NOT NULL,
        age     DECIMAL(3,0) NOT NULL,
        UNIQUE KEY uq_user_email (email),
        KEY idx_user_id (user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    with connection.cursor() as cur:
        cur.execute(ddl)
    connection.commit()
    # Match your sample output line:
    print("Table user_data created successfully")


# --------- Prototype 5 ----------
def insert_data(connection: MySQLConnection, data) -> None:
    """
    inserts data in the database if it does not exist.
    In this project, 'data' is a path to 'user_data.csv'.
    Deduplicates by UNIQUE(email).
    """
    # Accept either a path (string) or an iterable of dicts
    rows_iter: Iterable[Dict[str, str]]
    if isinstance(data, str):
        csv_path = data
        rows_iter = _read_csv_rows(csv_path)
    else:
        rows_iter = data  # assume iterable of dicts with keys name,email,age

    sql = """
    INSERT INTO user_data (user_id, name, email, age)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE email = email
    """

    with connection.cursor() as cur:
        batch = []
        for row in rows_iter:
            user_id = str(uuid.uuid4())
            name = row["name"].strip()
            email = row["email"].strip()
            age = int(row["age"])
            batch.append((user_id, name, email, age))

            # Executemany in chunks to keep memory reasonable
            if len(batch) >= 1000:
                cur.executemany(sql, batch)
                batch.clear()

        if batch:
            cur.executemany(sql, batch)

    connection.commit()


# --------- Generator for the objective ----------
def stream_users(connection: MySQLConnection, batch_size: int = 500
                 ) -> Generator[Dict[str, object], None, None]:
    """
    Lazily stream rows from user_data as dicts, one by one.
    This meets the 'generator that streams rows one by one' objective.
    """
    cur = connection.cursor(dictionary=True)
    try:
        cur.execute("SELECT user_id, name, email, age FROM user_data ORDER BY name;")
        while True:
            rows = cur.fetchmany(batch_size)
            if not rows:
                break
            for row in rows:
                # Convert Decimal to int for convenience
                if row.get("age") is not None:
                    try:
                        row["age"] = int(row["age"])
                    except Exception:
                        pass
                yield row
    finally:
        cur.close()


# --------- Helpers ----------
def _read_csv_rows(csv_path: str) -> Iterable[Dict[str, str]]:
    """Yield dict rows from a CSV with headers: name,email,age."""
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {"name": row["name"], "email": row["email"], "age": row["age"]}
