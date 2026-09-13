# ⚠️ MOCK GOVERNMENT DEMO PORTAL (MOCK / DEMO ONLY)

> **IMPORTANT DISCLAIMER**  
> This application is a simulated demonstration portal created exclusively for hackathon demonstration, automated agent evaluation, and human-in-the-loop workflow testing. It is **NOT** a government website and does **NOT** connect to any government database, identity provider, or SMS gateway.

---

## 1. Overview & Architecture

The Mock Portal simulates a realistic Indian e-governance service delivery portal (e.g., scheme application portal). It enforces standard security obstacles that typically block naïve web automation:

1. **Citizen Authentication**: Username & password check against dummy accounts.
2. **Anti-Bot CAPTCHA Challenge**: Requires human or AI visual perception to solve.
3. **Two-Factor OTP Security**: Simulated 6-digit one-time code (logged to server console, available via `/api/auth/otp/hint`).
4. **Scheme Application Form**: Pre-populated citizen details + required declarations.
5. **Final Submission & Receipt**: Issues unique reference acknowledgment numbers (`ACK-GOV-2026-XXXXXX`).

---

## 2. Test Credentials

| Username | Password | Role |
| :--- | :--- | :--- |
| `citizen_demo` | `Password123!` | Standard Citizen User |
| `admin_demo` | `AdminPass123!` | Portal Admin |
| `test_user` | `GovTest@2026` | Test Account |

---

## 3. How to Run Independently

### Backend (FastAPI - Port 8001)

```powershell
cd mock-portal/backend
python -m uvicorn app.main:app --port 8001 --reload
```
API Documentation will be available at: `http://localhost:8001/docs`

### Frontend (Vite + React - Port 5174)

```powershell
cd mock-portal/frontend
npm install
npm run dev
```
Mock Portal UI will be accessible at: `http://localhost:5174`

---

## 4. API Endpoints

- `POST /api/auth/login`: Authenticate dummy credentials & initialize session.
- `GET /api/auth/captcha?session_id=...`: Retrieve current session CAPTCHA puzzle.
- `POST /api/auth/captcha/verify`: Submit CAPTCHA answer; transitions to OTP step.
- `GET /api/auth/otp/hint?session_id=...`: Inspect simulated OTP code for testing.
- `POST /api/auth/otp/verify`: Submit 6-digit OTP code; transitions to application form.
- `GET /api/application/session?session_id=...`: Check session stage.
- `POST /api/application/submit`: Submit application form; issues acknowledgment receipt.
