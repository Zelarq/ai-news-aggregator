# AI News Digest Agent - Workspace Rules

Welcome to the AI News Digest Agent workspace. This ruleset primes the Antigravity IDE and its agent panels with the correct local development guidelines, memory footprints, and command run structures.

## Technology Stack & Environment
- **Runtime**: Python 3.11+
- **Environment**: Virtual environment located at `.\venv` (Windows)
- **Database**: Local SQLite database `news_digest.db`
- **Inference Layer**: Ollama local runtime serving **Llama 3.2 3B** (Memory footprint: ~2GB, optimized for 8GB RAM machines)
- **Email Interface**: SMTP Gmail App Password delivery

## Development Guidelines

1. **Module Execution**:
   Always execute scripts as modules using the `-m` flag from the root directory to ensure proper path resolution:
   - Run collector: `.\venv\Scripts\python -m src.collectors.youtube --test`
   - Run orchestrator: `.\venv\Scripts\python -m src.main --dry-run --test`

2. **API Safety**:
   - Never hardcode API keys or app secrets.
   - All credentials must be placed in a gitignored `.env` file.
   - The SQLite database file (`news_digest.db`) and any log files (`*.log`) must not be committed to Git.

3. **Inference Resilience**:
   Ensure that any LLM feature in `src/agent.py` degrades gracefully to keyword-based heuristics if the local Ollama service (`http://localhost:11434`) is offline, unreachable, or the model is not yet pulled.

## Command Reference

- **Dry-run (Local Preview)**:
  Runs the pipeline with mock collector data and heuristic LLM parsing, generating a local preview HTML file:
  ```powershell
  .\run_agent.bat --dry-run --test
  ```
- **Production Execution**:
  Runs the pipeline with real API queries and email delivery:
  ```powershell
  .\run_agent.bat
  ```
- **Local SQLite Shell**:
  ```powershell
  sqlite3 news_digest.db
  ```
