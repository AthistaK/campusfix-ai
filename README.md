# CampusFix AI

AI-powered campus incident intelligence platform.

## What it solves

Students often report the same campus problem multiple times through different channels. CampusFix converts those reports into structured incidents, detects related complaints, and prioritizes incidents.

## Killer feature

**AI Incident Clustering**

Example:

- "Wi-Fi is down in CSE block"
- "No internet on CSE second floor"
- "CSE lab cannot connect to Wi-Fi"

CampusFix can group related reports into one incident and increase its priority as more students report it.

## Stack

- Flask
- SQLite
- HTML/CSS/JavaScript
- Explainable rule-based AI engine

## Run locally

### 1. Create virtual environment

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Run

```bash
python app.py
```

The SQLite database is automatically created on first run.

## Demo flow

1. Open the dashboard.
2. Click **Report Problem**.
3. Enter:
   `Wi-Fi is completely down on the second floor of CSE Block since morning`
4. Select `CSE Block`.
5. Analyze the report.
6. The AI classifies it as Network and assigns severity/priority.
7. Submit it.
8. Submit a similar report again.
9. The system groups it into the existing incident and increases the report count.
10. Open the incident to inspect reports and change its status.

## Architecture

Browser
→ Flask API
→ AI decision engine
→ SQLite
→ Incident dashboard

## Future improvements

- LLM-based classification
- Embedding/vector similarity
- Real campus map
- Image classification
- Email/WhatsApp notifications
- Admin authentication
- Department assignment
- Live deployment
