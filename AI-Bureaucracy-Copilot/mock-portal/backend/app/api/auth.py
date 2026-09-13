import logging
import random
import string
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from app.sync import notify_main_portal

logger = logging.getLogger("mock_portal.auth")

router = APIRouter()

# In-memory sessions store
# session_id -> { username, step, captcha_code, otp_code, created_at, application_data }
_sessions: Dict[str, Dict[str, Any]] = {}

# Pre-configured dummy credentials
DUMMY_USERS = {
    "citizen_demo": "Password123!",
    "admin_demo": "AdminPass123!",
    "test_user": "GovTest@2026",
}


class LoginRequest(BaseModel):
    username: str
    password: str
    run_id: Optional[str] = None


class LoginResponse(BaseModel):
    session_id: str
    username: str
    current_step: str
    message: str


class CaptchaVerifyRequest(BaseModel):
    session_id: str
    captcha_response: str


class OtpVerifyRequest(BaseModel):
    session_id: str
    otp_code: str


def get_session_or_404(session_id: str) -> Dict[str, Any]:
    clean_id = session_id.strip() if session_id else ""
    if not clean_id or clean_id not in _sessions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active portal session not found or expired. Please login again.",
        )
    return _sessions[clean_id]


def generate_captcha_text(length: int = 5) -> str:
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))


@router.post("/auth/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest):
    uname = payload.username.strip()
    pwd = payload.password.strip()

    if uname not in DUMMY_USERS or DUMMY_USERS[uname] != pwd:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid mock credentials. Use 'citizen_demo' / 'Password123!'.",
        )

    session_id = str(uuid.uuid4())
    captcha_code = generate_captcha_text()

    _sessions[session_id] = {
        "session_id": session_id,
        "username": uname,
        "step": "CAPTCHA",
        "captcha_code": captcha_code,
        "otp_code": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "application_data": None,
        "run_id": payload.run_id,
    }

    logger.info(f"[MOCK PORTAL] Citizen '{uname}' logged in. Session '{session_id}' -> CAPTCHA required.")

    # Synchronize login completion with main Copilot backend
    if payload.run_id:
        notify_main_portal(
            run_id=payload.run_id,
            action_type="LOGIN",
            status="LOGIN_COMPLETED",
            portal_session_id=session_id,
        )

    return LoginResponse(
        session_id=session_id,
        username=uname,
        current_step="CAPTCHA",
        message="Login successful. Please solve the security CAPTCHA puzzle.",
    )



@router.get("/auth/captcha")
def get_captcha(session_id: str = Query(..., description="Active session ID")):
    session = get_session_or_404(session_id)

    if session["step"] != "CAPTCHA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid step progression. Current step is '{session['step']}'.",
        )

    captcha_code = session["captcha_code"]
    return {
        "session_id": session_id,
        "captcha_text": captcha_code,
        "instructions": "Type the 5 characters shown above exactly as displayed.",
    }


@router.post("/auth/captcha/verify")
def verify_captcha(payload: CaptchaVerifyRequest):
    session = get_session_or_404(payload.session_id)

    if session["step"] != "CAPTCHA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot verify CAPTCHA when current step is '{session['step']}'.",
        )

    expected = session["captcha_code"].upper()
    provided = payload.captcha_response.strip().upper()

    if provided != expected:
        # Regenerate captcha on failure
        session["captcha_code"] = generate_captcha_text()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect CAPTCHA text. A new CAPTCHA has been generated.",
        )

    # Generate 6-digit OTP code
    simulated_otp = f"{random.randint(100000, 999999)}"
    session["otp_code"] = simulated_otp
    session["step"] = "OTP"

    logger.info(f"============================================================")
    logger.info(f"[MOCK PORTAL CONSOLE] Simulated OTP for session '{payload.session_id}': {simulated_otp}")
    logger.info(f"============================================================")

    # Synchronize CAPTCHA completion with main Copilot backend
    run_id = session.get("run_id")
    if run_id:
        notify_main_portal(
            run_id=run_id,
            action_type="CAPTCHA",
            status="CAPTCHA_COMPLETED",
            portal_session_id=payload.session_id,
        )

    return {
        "session_id": payload.session_id,
        "current_step": "OTP",
        "message": f"CAPTCHA solved successfully. Simulated OTP has been generated (hint available in console/API).",
    }


@router.get("/auth/otp/hint")
def get_otp_hint(session_id: str = Query(..., description="Active session ID")):
    """Development / Testing endpoint to inspect simulated OTP without SMS."""
    session = get_session_or_404(session_id)
    if session["step"] != "OTP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OTP is only active when session step is 'OTP'. Current step: '{session['step']}'.",
        )
    return {
        "session_id": session_id,
        "otp_hint": session["otp_code"],
        "note": "For mock/testing purposes only. Real portals dispatch via SMS.",
    }


@router.post("/auth/otp/verify")
def verify_otp(payload: OtpVerifyRequest):
    session = get_session_or_404(payload.session_id)

    if session["step"] != "OTP":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot verify OTP when current step is '{session['step']}'.",
        )

    expected_otp = session["otp_code"]
    provided_otp = payload.otp_code.strip()

    if provided_otp != expected_otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please enter the simulated 6-digit code.",
        )

    session["step"] = "APPLICATION_FORM"
    logger.info(f"[MOCK PORTAL] OTP verified for session '{payload.session_id}'. Ready for application form.")

    # Synchronize OTP verification with main Copilot backend
    run_id = session.get("run_id")
    if run_id:
        notify_main_portal(
            run_id=run_id,
            action_type="OTP",
            status="OTP_COMPLETED",
            portal_session_id=payload.session_id,
        )

    return {
        "session_id": payload.session_id,
        "current_step": "APPLICATION_FORM",
        "message": "Two-Factor OTP verified successfully. You may now complete your scheme application form.",
    }



def clear_sessions_for_testing():
    _sessions.clear()
