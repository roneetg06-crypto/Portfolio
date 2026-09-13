@echo off
echo ========================================================
echo Starting Full AI Bureaucracy Copilot Ecosystem (All 4 Services)
echo ========================================================

start "Copilot Backend (Port 8000)" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --port 8000 --reload"

start "Copilot Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

start "Mock Portal Backend (Port 8001)" cmd /k "cd /d %~dp0mock-portal\backend && python -m uvicorn app.main:app --port 8001 --host 0.0.0.0 --reload"

start "Mock Portal Frontend (Port 5174)" cmd /k "cd /d %~dp0mock-portal\frontend && npm run dev"

echo.
echo All services are launching:
echo 1. Citizen Copilot Frontend:     http://localhost:5173
echo 2. Citizen Copilot Backend:      http://localhost:8000
echo 3. Mock Government Portal UI:    http://localhost:5174
echo 4. Mock Government Portal API:   http://localhost:8001
echo.
