@echo off
echo ========================================================
echo Starting Mock Government Portal (Backend 8001 + Frontend 5174)
echo ========================================================

start "Mock Portal Backend (Port 8001)" cmd /k "cd /d %~dp0mock-portal\backend && python -m uvicorn app.main:app --port 8001 --host 0.0.0.0 --reload"

start "Mock Portal Frontend (Port 5174)" cmd /k "cd /d %~dp0mock-portal\frontend && npm run dev"

echo.
echo Mock Portal is launching:
echo Backend:  http://localhost:8001
echo Frontend: http://localhost:5174
echo.
