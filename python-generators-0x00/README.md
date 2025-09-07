# 0. Getting started with Python Generators

**Goal:** Create a generator that streams rows from a SQL database one by one.

This project seeds a MySQL database and demonstrates a streaming **generator** that yields rows from the `user_data` table without loading everything into memory.

## Requirements
- Python 3.10+
- MySQL running locally
- `pip install mysql-connector-python`

## Environment Variables (optional)
You can configure MySQL connection via env vars (defaults in parentheses):
- `MYSQL_HOST` (`127.0.0.1`)
- `MYSQL_PORT` (`3306`)
- `MYSQL_USER` (`root`)
- `MYSQL_PASSWORD` (empty)

## Files
- `seed.py` — Database setup, CSV load, and the generator `stream_users(...)`.
- `0-main.py` — Provided test harness (imports `seed` and runs setup + a quick query).
- `user_data.csv` — Sample dataset.

## Schema
Database: `ALX_prodev`  
Table: `user_data`
- `user_id` `CHAR(36)` **PRIMARY KEY** (UUIDv4) + index  
- `name` `VARCHAR(255)` **NOT NULL**  
- `email` `VARCHAR(255)` **NOT NULL**, **UNIQUE** (prevents duplicates)  
- `age` `DECIMAL(3,0)` **NOT NULL**

## Usage
```bash
python3 0-main.py
