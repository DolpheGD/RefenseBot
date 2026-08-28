# RefenseBot

**RefenseBot** is an AI-powered Discord moderation bot built around the philosophy of **Refense** the balance between **offense** and **defense**.

---

## Core Idea

Every message is analyzed and scored across three major categories:

* **Hate**
  Covers toxicity, harassment, threats, and violent intent.

* **Sexual**
  Covers sexual content, including severe escalations.

* **Concern**
  Covers self-harm and distress indicators.

* **Scam**
  Covers scam indicators, typically from Mr. Beast scams

These scores are combined into a **Danger Score**, which contributes to a persistent user risk profile.

Instead of averaging all messages, Refender stores the **Top 10 most dangerous messages** from each user and calculates their overall danger based on those peak behaviors.

This preserves important signals and prevents dangerous behavior from being diluted by normal conversation.

---

## Setup

1. Clone the repo and run the bootstrap script from the project root:
   * Windows: double-click `setup.bat` (or run `python setup_bot.py`)
   * macOS/Linux: `./setup.sh` (or `python3 setup_bot.py`)

   This creates a `.venv` virtual environment, installs everything in
   `requirements.txt`, generates a starter `.env` from `.env.example`, and
   creates the local SQLite database tables.
2. Fill in `.env` with your `BOT_KEY`, `SERVER_ID`, `HF_TOKEN`, and `TOPGG_TOKEN`.
3. Re-run the setup script (or `python -m bot.database.db_init`) if you filled
   in `.env` after the first run, so the database step can complete.
4. Activate the virtual environment and start the bot:
   * Windows: `.venv\Scripts\activate`
   * macOS/Linux: `source .venv/bin/activate`
   * `python start_bot.py`

---

## Features

### AI-Powered Text Moderation

Uses multiple machine learning models to classify message content:

* KoalaAI moderation model
* Toxic-BERT ensemble scoring
* FalconsAI NSFW scoring
* EasyOCR for image text extraction

---

### Behavioral Risk Profiling

Tracks:

* User danger score
* Flagged message count
* Category averages
* Top 10 most dangerous messages

---

### Slash Command Interface

#### Classification

`/classify text`

Classify raw text input.

`/classify id`

Classify an existing message by ID.

`/classify user`

Classify a user's danger level

---

#### Risk Analysis

`/leaderboard`

Display the highest-risk users in the server.

---

#### Voting Integration with Top.gg

Votes are detected by polling top.gg's v1 REST API directly (plain `aiohttp`
calls, no wrapper library) on a timer - there's no inbound webhook or public
port to expose, the bot checks and credits votes itself. `TOPGG_TOKEN` must be
a v1 token from your project's "Integrations & API" settings on top.gg -
older, webhook-era tokens are legacy/v0-only and will silently fail v1 auth.

`/vote link`

Display the vote link and when the user may vote again.

`/vote allow`

Allows admin to enable server-specific voting policies.

`/vote spend`

Only for Administrator allowed servers, enables users to use voting credit to control message history.

---

#### User Utility

`/achievements`

Display various achievements the user can get from their stats

`/help`

Display information for all the commands to the user

---

## Architecture

Refender is structured for scalability:

## Database Design

### Guild

Stores:

* Guild ID
* Guild Name
* Vote enable option

The bot runs on a per-server database, so each danger rating for a user is specific to that server.

### UserProfile

Stores:

* Discord ID
* Username
* Danger Score
* Total Messages
* Cached other user data
* Voting information

---

### DangerMessage

Stores:

* Message content
* Timestamp
* Category scores
* Danger score

Each user keeps only their highest-risk messages for efficient behavioral modeling.

---

## Tech Stack

* Python
* discord.py
* SQLAlchemy
* SQLite
* Hugging Face Transformers
* PyTorch
* topggpy

---

## Future Goals

* Auto purge Mr Beast scams
* GIF moderation
* Video frame analysis
* User trend analysis
* Server-wide toxicity heatmaps
* Custom model fine-tuning on collected moderation data
* Multimodal risk fusion

---

## Disclaimer

AI moderation is imperfect.

Refender is designed to assist moderators, not replace them.
Context, intent, and human judgment remain critical.

