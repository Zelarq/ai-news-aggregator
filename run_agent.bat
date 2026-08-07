@echo off
:: Navigate to the absolute project workspace directory
cd /d "D:\collage\ai-news-aggregator"

:: Force UTF-8 output so Unicode characters in news titles don't crash Windows console
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

:: Execute the news aggregator orchestrator with the virtual environment's python, passing any CLI arguments
".\venv\Scripts\python.exe" -m src.main %*
