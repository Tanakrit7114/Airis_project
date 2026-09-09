@echo off
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (set PYTHON=.venv\Scripts\python.exe) else (set PYTHON=python)
%PYTHON% -m uvicorn app.server.main:app --host 127.0.0.1 --port 8001
