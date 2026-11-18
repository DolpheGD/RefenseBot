import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import setup_bot
from setup_bot import backup_database


class DatabaseBackupTests(unittest.TestCase):
    def test_backup_copies_database_and_preserves_existing_backups(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database_file = root / "cascadebot.db"
            backup_dir = root / "DB_Backups"
            database = sqlite3.connect(database_file)
            try:
                database.execute("CREATE TABLE sample (value TEXT)")
                database.execute("INSERT INTO sample VALUES ('persisted')")
                database.commit()
            finally:
                database.close()

            first_backup = backup_database(database_file, backup_dir)
            second_backup = backup_database(database_file, backup_dir)

            self.assertIsNotNone(first_backup)
            self.assertIsNotNone(second_backup)
            self.assertNotEqual(first_backup, second_backup)
            self.assertEqual(len(list(backup_dir.glob("cascadebot_*.db"))), 2)
            database = sqlite3.connect(first_backup)
            try:
                value = database.execute("SELECT value FROM sample").fetchone()[0]
            finally:
                database.close()

        self.assertEqual(value, "persisted")

    def test_missing_database_does_not_create_backup_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            backup_dir = root / "DB_Backups"

            result = backup_database(root / "missing.db", backup_dir)

        self.assertIsNone(result)
        self.assertFalse(backup_dir.exists())

    def test_setup_initializes_then_backs_up_a_new_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database_file = root / "cascadebot.db"
            backup_dir = root / "DB_Backups"

            def initialize_database(*_args, **_kwargs):
                database = sqlite3.connect(database_file)
                try:
                    database.execute("CREATE TABLE initialized (value INTEGER)")
                    database.commit()
                finally:
                    database.close()
                return SimpleNamespace(returncode=0)

            with (
                patch.object(setup_bot, "DATABASE_FILE", database_file),
                patch.object(setup_bot, "DATABASE_BACKUP_DIR", backup_dir),
                patch.object(setup_bot, "venv_python", return_value=root / "python.exe"),
                patch.object(
                    setup_bot.subprocess,
                    "run",
                    side_effect=initialize_database,
                ),
            ):
                setup_bot.init_database()

            backups = list(backup_dir.glob("cascadebot_*.db"))
            self.assertEqual(len(backups), 1)
            backup = sqlite3.connect(backups[0])
            try:
                tables = backup.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            finally:
                backup.close()
            self.assertIn(("initialized",), tables)


if __name__ == "__main__":
    unittest.main()
