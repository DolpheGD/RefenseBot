from sqlalchemy import text
from bot.database.db import engine

with engine.begin() as conn:
    conn.execute(text("""
        UPDATE user_profiles
        SET votes_used = 0, votes = 0
    """))