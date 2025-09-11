#!/usr/bin/python3
"""
3-concurrent.py

Run multiple SQLite queries concurrently using aiosqlite + asyncio.gather.

- async_fetch_users(): fetches all users
- async_fetch_older_users(): fetches users older than 40
- fetch_concurrently(): runs both concurrently and prints results
"""

import asyncio
import aiosqlite


DB_PATH = "users.db"


async def async_fetch_users():
    """Fetch all users (returns list of tuples)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users;") as cur:
            rows = await cur.fetchall()
            return rows


async def async_fetch_older_users():
    """Fetch users with age > 40 (returns list of tuples)."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE age > ?;", (40,)) as cur:
            rows = await cur.fetchall()
            return rows


async def fetch_concurrently():
    """Execute both queries concurrently and print the results."""
    all_users, older_users = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users(),
    )

    print("All users:", all_users)
    print("Users older than 40:", older_users)

    return all_users, older_users


if __name__ == "__main__":
    # Run the concurrent fetch
    asyncio.run(fetch_concurrently())
