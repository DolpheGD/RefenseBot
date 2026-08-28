#!/usr/bin/env python3
"""
setup_bot.py - one-shot environment bootstrapper for RefenseBot.

What this does:
  1. Creates a local virtual environment in .venv (if one doesn't already exist)
  2. Upgrades pip/setuptools/wheel inside that venv
  3. Installs everything listed in requirements.txt
  4. Creates a starter .env (from .env.example) if you don't have one yet
  5. Creates the SQLite database tables (safe to re-run - it's idempotent)

Usage:
    python setup_bot.py

Then activate the venv and run the bot:
    Windows:     .venv\\Scripts\\activate
    macOS/Linux: source .venv/bin/activate
    python start_bot.py

You can re-run this script any time (e.g. after pulling new dependencies) -
every step skips or no-ops safely if it's already done.
"""

import platform
import subprocess
import sys
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

REQUIRED_ENV_KEYS = ("BOT_KEY", "SERVER_ID")

ENV_TEMPLATE = """\
# Discord bot token (Discord Developer Portal -> your application -> Bot -> Token)
BOT_KEY=

# The Discord server (guild) ID used for instant slash-command sync in dev mode
SERVER_ID=

# True while developing locally (syncs commands to SERVER_ID only, instantly).
# False in production (syncs commands globally, can take up to an hour to appear).
DEV_MODE=True

# Hugging Face access token, used to download the moderation models
HF_TOKEN=

# top.gg API token for this bot. Find it on top.gg -> your bot's page -> Webhooks
# tab (listed as "Authorization" / API token). Used to poll top.gg for votes -
# no public server or webhook needed.
TOPGG_TOKEN=
"""


def venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run(cmd):
    print(f"\n$ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print(f"\nCommand failed (exit code {result.returncode}): {' '.join(str(c) for c in cmd)}")
        sys.exit(result.returncode)


def check_python_version():
    if sys.version_info < (3, 10):
        print(f"Python 3.10+ is required to bootstrap this project. You have {platform.python_version()}.")
        sys.exit(1)
    print(f"Using Python {platform.python_version()} to bootstrap the environment.")


def create_venv():
    if VENV_DIR.exists():
        print(f"Virtual environment already exists at {VENV_DIR} - skipping creation.")
        return
    print(f"Creating virtual environment at {VENV_DIR} ...")
    venv.EnvBuilder(with_pip=True, upgrade_deps=True).create(VENV_DIR)


def install_requirements():
    py = venv_python()
    if not REQUIREMENTS.exists():
        print("requirements.txt not found - skipping dependency install.")
        return
    run([str(py), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    print("\nInstalling requirements.txt (this can take a while - torch/easyocr are large) ...")
    run([str(py), "-m", "pip", "install", "-r", str(REQUIREMENTS)])


def ensure_env_example():
    if ENV_EXAMPLE.exists():
        return
    ENV_EXAMPLE.write_text(ENV_TEMPLATE, encoding="utf-8")
    print(f"Created {ENV_EXAMPLE.name} template.")


def ensure_env_file():
    ensure_env_example()
    if ENV_FILE.exists():
        print(".env already exists - leaving it as-is.")
        return
    ENV_FILE.write_text(ENV_TEMPLATE, encoding="utf-8")
    print(
        "\nCreated a blank .env from .env.example.\n"
        "Open .env and fill in BOT_KEY, SERVER_ID, HF_TOKEN and TOPGG_TOKEN before running the bot."
    )


def env_is_configured() -> bool:
    """Best-effort check that the required keys are actually filled in."""
    if not ENV_FILE.exists():
        return False

    values = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()

    return all(values.get(key) for key in REQUIRED_ENV_KEYS)


def init_database():
    if not env_is_configured():
        print(
            "\nSkipping database setup: BOT_KEY/SERVER_ID aren't filled in yet.\n"
            "Fill in .env, then re-run this script (or run: python -m bot.database.db_init)."
        )
        return

    py = venv_python()
    print("\nCreating/verifying database tables ...")
    result = subprocess.run([str(py), "-m", "bot.database.db_init"], cwd=str(ROOT))
    if result.returncode != 0:
        print("Database initialization failed - check the error above and re-run this script once fixed.")


def print_next_steps():
    activate = r".venv\Scripts\activate" if platform.system() == "Windows" else "source .venv/bin/activate"
    print(
        "\n" + "=" * 60 +
        "\nSetup complete!\n\n"
        "1. Fill in your .env file (BOT_KEY, SERVER_ID, HF_TOKEN, TOPGG_TOKEN) if you haven't yet.\n"
        f"2. Activate the virtual environment:\n     {activate}\n"
        "3. Run the bot:\n     python start_bot.py\n"
        + "=" * 60
    )


def main():
    check_python_version()
    create_venv()
    install_requirements()
    ensure_env_file()
    init_database()
    print_next_steps()


if __name__ == "__main__":
    main()
