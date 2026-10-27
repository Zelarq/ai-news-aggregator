# AI News Aggregator & Auto-Digest

A fully automated, local-first Python pipeline that aggregates, deduplicates, and summarizes AI-related news from multiple sources (Hacker News, Reddit, YouTube). It leverages local LLM inference via Ollama to generate concise summaries and strictly categorize news items. The final output is composed into a styled HTML email and delivered daily.

## 🚀 Key Features
* **Multi-Source Ingestion:** Fetches top stories and trends from Hacker News, Reddit, and YouTube.
* **Local LLM Summarization:** Uses `qwen2.5-coder:3b` (or `llama3.2:3b`) via Ollama and LangChain to generate high-quality 2-3 sentence summaries entirely locally (with a keyword heuristic fallback).
* **Automated Categorization:** Classifies articles into strict categories (Model Release, Research Paper, Tool/Framework, Industry News, Community Discussion).
* **Smart Deduplication:** Uses a local SQLite database to track processed articles and prevent duplicate emails.
* **Zero-Touch Automation:** Runs silently in the background daily via Windows Task Scheduler.
* **HTML Email Delivery:** Composes a clean, responsive HTML digest and sends it via Gmail SMTP.

## 🛠️ Technology Stack
* **Language:** Python 3.11+
* **Database:** SQLite (local state management)
* **AI / ML:** LangChain, Ollama (Qwen 2.5 Coder 3B / Llama 3.2 3B)
* **APIs:** Hacker News (Firebase REST), YouTube Data API v3, Reddit (PRAW)
* **Automation:** PowerShell, Windows Task Scheduler, SMTP (MIMEMultipart)

## 📦 Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/ai-news-aggregator.git
   cd ai-news-aggregator
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Copy `.env.example` to `.env` and fill in your details:
   ```env
   GMAIL_ADDRESS=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_app_password
   DIGEST_RECIPIENT=your_email@gmail.com
   # Optional: Add Reddit and YouTube API keys
   ```

5. **(Optional) Setup Ollama:**
   Download and install Ollama, then run:
   ```bash
   ollama pull llama3.2:3b
   ```

## ⚙️ Usage

**Run locally (Test Mode):**
Does not send emails, uses mock data to test the pipeline.
```bash
.\run_agent.bat --dry-run --test
```

**Run production:**
Fetches live data, generates summaries, and sends the email.
```bash
.\run_agent.bat
```

**Automate Daily Runs:**
Run the provided PowerShell script to register a daily Windows Scheduled Task.
```powershell
powershell -ExecutionPolicy Bypass -File .\setup_schedule.ps1
```

## 📝 Architecture Workflow
1. **Collector Modules:** Poll APIs based on a lookback window (e.g., 24 hours), filter out noise using keywords.
2. **Database:** Save raw items. If an item already exists (`external_id`), it is skipped.
3. **Agent:** Unsummarized items are sent to the local LLM. LangChain extracts a JSON schema containing a category and a summary.
4. **Composer:** Group items by category and inject them into an HTML template.
5. **Mailer:** Send the composed template via SMTP. Marked items as "sent" in SQLite.
