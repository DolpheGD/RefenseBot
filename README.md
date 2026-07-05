# Refender

**Refender** is an AI-powered Discord moderation bot built around the philosophy of **Refense** the balance between **offense** and **defense**.

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

`/clear`

Admin-only command to clear a user's danger history.

---

## Architecture

Refender is structured for scalability:

## Database Design

### UserProfile

Stores:

* Discord ID
* Username
* Danger Score
* Total Messages
* Cached other user data

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

