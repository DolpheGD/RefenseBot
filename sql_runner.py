from sqlalchemy import text
from bot.database.db import engine

with engine.begin() as conn:
    conn.execute(text("""
        ALTER TABLE guilds
        ADD COLUMN allow_votes BOOLEAN NOT NULL DEFAULT FALSE
    """))