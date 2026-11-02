from sqlalchemy import inspect, text

from bot.database.db import engine
from bot.database.models.user_model import Base


def init_db():
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    danger_message_columns = {column["name"] for column in inspector.get_columns("danger_messages")}
    if "image_url" not in danger_message_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE danger_messages ADD COLUMN image_url VARCHAR"))


if __name__ == "__main__":
    init_db()


