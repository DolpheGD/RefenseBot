from sqlalchemy import create_engine

DB_URL = "sqlite:///cascadebot.db"

engine = create_engine(
    DB_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)