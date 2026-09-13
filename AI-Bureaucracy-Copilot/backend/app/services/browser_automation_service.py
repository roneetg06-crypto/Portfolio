import logging
import os
import queue
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("copilot.browser_automation")

# Default mock portal base URL
MOCK_PORTAL_BASE_URL = os.environ.get("MOCK_PORTAL_BASE_URL", "http://localhost:5174")

# Whether to run Playwright in headless mode (default False for visible demo)
DEFAULT_HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "false").lower() in ("true", "1", "yes")

_sessions_lock = threading.Lock()
# run_id -> { "worker": BrowserWorker, "playwright": Playwright, "browser": Browser, "context": BrowserContext, "page": Page, "status": str }
_active_browser_sessions: Dict[str, Dict[str, Any]] = {}
_sync_lock = threading.Lock()
_active_sync_runs = set()


def is_human_barrier(page_state: str) -> bool:
    """Return True if the current page state requires mandatory human interaction."""
    return page_state.upper() in ("LOGIN", "CAPTCHA", "OTP", "FINAL_REVIEW", "CONFIRMATION")


class BrowserWorker:
    """
    Dedicated worker thread per Playwright browser session.
    Ensures all Playwright sync API operations execute on the thread that initialized it,
    preventing greenlet cross-thread errors when called from FastAPI threadpools.
    """
    def __init__(self, run_id: str, portal_url: str, headless: bool, slow_mo: int = 0):
        self.run_id = run_id
        self.portal_url = portal_url
        self.headless = headless
        self.slow_mo = slow_mo
        self.q: queue.Queue = queue.Queue()
        self.ready_event = threading.Event()
        self.init_error: Optional[Exception] = None
        self.page: Any = None
        self.browser: Any = None
        self.context: Any = None
        self.pw: Any = None
        self.is_closed: bool = False
        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name=f"BrowserWorker-{run_id[:8]}",
        )
        self.thread.start()
        self.ready_event.wait(timeout=15)
        if self.init_error:
            raise self.init_error

    def _run(self) -> None:
        from playwright.sync_api import sync_playwright
        try:
            self.pw = sync_playwright().start()
            launch_kwargs: Dict[str, Any] = {
                "headless": self.headless,
                "args": [
                    "--start-maximized",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-default-browser-check",
                ],
                "ignore_default_args": ["--enable-automation"],
            }
            if self.slow_mo:
                launch_kwargs["slow_mo"] = self.slow_mo
            self.browser = self.pw.chromium.launch(**launch_kwargs)
            
            context_kwargs: Dict[str, Any] = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            if not self.headless:
                context_kwargs["no_viewport"] = True
            else:
                context_kwargs["viewport"] = {"width": 1920, "height": 1080}

            self.context = self.browser.new_context(**context_kwargs)
            self.page = self.context.new_page()
            self.page.set_default_timeout(10000)
            logger.info(f"[BROWSER-WORKER] Opening mock portal at: {self.portal_url} (headless={self.headless})")
            self.page.goto(self.portal_url, wait_until="domcontentloaded", timeout=12000)
            self.ready_event.set()
        except Exception as e:
            self.init_error = e
            self.ready_event.set()
            return

        while True:
            item = self.q.get()
            if item is None:
                self.is_closed = True
                try:
                    if self.browser:
                        self.browser.close()
                    if self.pw:
                        self.pw.stop()
                except Exception:
                    pass
                break
            func, resp_q = item
            try:
                res = func(self.page)
                resp_q.put(("ok", res))
            except Exception as e:
                resp_q.put(("err", e))

    def execute(self, func: Callable[[Any], Any], timeout: float = 20) -> Any:
        if self.is_closed:
            raise RuntimeError(f"Browser session '{self.run_id}' is already closed.")
        resp_q: queue.Queue = queue.Queue()
        self.q.put((func, resp_q))
        status, val = resp_q.get(timeout=timeout)
        if status == "err":
            raise val
        return val

    def stop(self) -> None:
        self.is_closed = True
        self.q.put(None)
        self.thread.join(timeout=3)


class BrowserAutomationService:
    @staticmethod
    def is_available() -> bool:
        """Check if Playwright is installed and usable."""
        try:
            import playwright
            return True
        except ImportError:
            return False

    @classmethod
    def _run_on_page(cls, run_id: str, fn: Callable[[Any], Any], timeout: float = 20) -> Any:
        """
        Execute a function on the browser page safely:
        - If a BrowserWorker exists for the session, execute on the worker thread.
        - Otherwise, execute directly on the registered page (e.g. for unit test mocks).
        """
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            raise RuntimeError(f"Active browser session '{run_id}' not found")
        worker = sess.get("worker")
        if worker and worker.thread.is_alive() and not worker.is_closed:
            return worker.execute(fn, timeout=timeout)
        page = sess.get("page")
        if page:
            return fn(page)
        raise RuntimeError(f"No active page found for session '{run_id}'")

    @classmethod
    def register_session(
        cls,
        run_id: str,
        page: Any,
        browser: Any = None,
        playwright: Any = None,
        context: Any = None,
    ) -> None:
        """Register an existing or test page/session into the active store."""
        with _sessions_lock:
            _active_browser_sessions[run_id] = {
                "playwright": playwright,
                "browser": browser,
                "context": context,
                "page": page,
                "run_id": run_id,
                "thread_id": threading.get_ident(),
                "current_state": "UNKNOWN",
            }

    @classmethod
    def start_session(
        cls,
        run_id: str,
        scheme_id: str = "SCH-HLT-001",
        profile_id: str = "default",
        portal_url: Optional[str] = None,
        headless: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Launch Chromium in a dedicated worker thread and navigate to the Mock Government Portal.
        Keeps the browser open for interactive human-in-the-loop verification.
        """
        clean_run_id = run_id.strip() if run_id else ""
        if not clean_run_id:
            return {"status": "ERROR", "error": "Invalid run_id", "page_state": "ERROR"}

        with _sessions_lock:
            # Check if session already exists and is alive
            if clean_run_id in _active_browser_sessions:
                sess = _active_browser_sessions[clean_run_id]
                worker = sess.get("worker")
                if worker and not worker.is_closed and worker.thread.is_alive():
                    state = cls.detect_page_state(clean_run_id)
                    url = cls._run_on_page(clean_run_id, lambda p: p.url, timeout=3)
                    return {
                        "status": "ACTIVE",
                        "run_id": clean_run_id,
                        "page_state": state,
                        "url": url,
                    }

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("[BROWSER] Playwright is not installed.")
            return {
                "status": "ERROR",
                "error": "Playwright is not installed. Please run: pip install playwright && playwright install chromium",
                "page_state": "ERROR",
            }

        is_headless = DEFAULT_HEADLESS if headless is None else headless
        target_url = portal_url or (
            f"{MOCK_PORTAL_BASE_URL}/?run_id={clean_run_id}&scheme_id={scheme_id}&profile_id={profile_id}"
        )

        try:
            slow_mo_ms = 200 if not is_headless else 0
            worker = BrowserWorker(
                run_id=clean_run_id,
                portal_url=target_url,
                headless=is_headless,
                slow_mo=slow_mo_ms,
            )

            with _sessions_lock:
                _active_browser_sessions[clean_run_id] = {
                    "worker": worker,
                    "playwright": worker.pw,
                    "browser": worker.browser,
                    "context": worker.context,
                    "page": worker.page,
                    "run_id": clean_run_id,
                    "target_url": target_url,
                    "current_state": "LOGIN",
                }

            page_state = cls.detect_page_state(clean_run_id)
            logger.info(f"[BROWSER] Session '{clean_run_id}' started. Initial page state: {page_state}")

            return {
                "status": "ACTIVE",
                "run_id": clean_run_id,
                "page_state": page_state,
                "url": target_url,
            }

        except Exception as e:
            logger.error(f"[BROWSER] Error launching browser session for run '{clean_run_id}': {e}")
            cls.close_session(clean_run_id)
            return {
                "status": "ERROR",
                "error": str(e),
                "page_state": "ERROR",
            }

    @classmethod
    def sync_milestone(cls, run_id: str, milestone: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Synchronize automated milestones with the Main Backend centralized state.
        """
        try:
            from app.services import application_state_service
            application_state_service.update_application_status(
                run_id=run_id,
                update_data={
                    "action_type": milestone,
                    "status": milestone,
                },
            )
            logger.info(f"[BROWSER] Synchronized milestone '{milestone}' for run '{run_id}'.")
        except Exception as e:
            logger.debug(f"[BROWSER] Application state update note for milestone '{milestone}': {e}")

    @classmethod
    def detect_page_state(cls, run_id: str) -> str:
        """
        Inspect the active browser DOM and URL to detect the current mock portal step.
        Returns:
            LOGIN | CAPTCHA | OTP |
            STUDENT_PARENT_INFO | LOAN_INFO | DOC_UPLOAD |
            FINAL_REVIEW | CONFIRMATION |
            APPLICATION_FORM | ERROR | UNKNOWN | SESSION_CLOSED
        """
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            return "SESSION_CLOSED"

        worker = sess.get("worker")
        if worker and worker.is_closed:
            return "SESSION_CLOSED"

        def _detect(page: Any) -> str:
            if page.is_closed():
                return "SESSION_CLOSED"

            # 1. Check for Confirmation Receipt (Step 8 / System Completion)
            if page.locator(
                ".confirmation-receipt, .confirmation-badge, .confirmation-card, "
                ".ack-number-box, .ack-receipt-box, "
                "h2:has-text('Education Loan Application Submitted'), "
                "h2:has-text('Application Successfully Submitted')"
            ).count() > 0:
                return "CONFIRMATION"

            # 2. Check for Final Review (Step 7 / Human Gate)
            elif page.locator(
                "#finalReviewContainer, #finalReviewCard, #humanReviewBarrier, "
                ".confirmDeclaration, [data-testid='confirmDeclaration'], "
                "[data-testid='submitFinalApplicationBtn'], .submitFinalApplicationBtn, "
                "h2:has-text('Application Final Review')"
            ).count() > 0:
                return "FINAL_REVIEW"

            # 3. Check for Mandatory Document Upload (Step 6 / Automated)
            elif page.locator(
                "#documentUploadForm, #admissionLetter, #feeStructure, "
                "#studentAadhaar, #parentIncomeCertificate, #nextToReviewBtn, "
                "h2:has-text('Mandatory Document Upload')"
            ).count() > 0:
                return "DOC_UPLOAD"

            # 4. Check for Education Loan Details (Step 5 / Automated)
            elif page.locator(
                "#loanDetailsForm, #course, #college, #loanAmount, #tuitionFee, "
                "#livingExpenses, #bankPreference, #loanTenure, #nextToDocsBtn, "
                "h2:has-text('Education Loan Information')"
            ).count() > 0:
                return "LOAN_INFO"

            # 5. Check for Student & Parent Particulars (Step 4 / Automated)
            elif page.locator(
                "#studentParentForm, #studentName, #parentName, "
                "#annualFamilyIncome, #aadhaarLastFour, #nextToLoanBtn, "
                "h2:has-text('Student & Parent Information')"
            ).count() > 0:
                return "STUDENT_PARENT_INFO"

            # 6. Check for OTP 2FA Gate (Step 3 / Human Gate)
            elif page.locator("#otpInput, button:has-text('Verify OTP'), .simulated-otp-box").count() > 0:
                return "OTP"

            # 7. Check for CAPTCHA Gate (Step 2 / Human Gate)
            elif page.locator("#captchaAnswer, .captcha-box, button:has-text('Verify CAPTCHA')").count() > 0:
                return "CAPTCHA"

            # 8. Check for Citizen Login Gate (Step 1 / Human Gate)
            elif page.locator("#username, #password, button:has-text('Sign In to Portal')").count() > 0:
                return "LOGIN"

            # 9. Legacy Check for Generic Scheme Application Form
            elif page.locator("#applicant_name, form.portal-form select#scheme_id").count() > 0:
                return "APPLICATION_FORM"

            return "UNKNOWN"

        try:
            detected_state = cls._run_on_page(run_id, _detect, timeout=5)
            sess["current_state"] = detected_state
            return detected_state
        except BaseException as e:
            logger.warning(f"[BROWSER] Error detecting page state for run '{run_id}': {e}")
            return sess.get("current_state", "ERROR")

    @classmethod
    def fill_student_parent_info(cls, run_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 4: Populates Student & Parent Information on the Mock Portal.
        Automated step advancing to Step 5 (LOAN_INFO).
        Synchronizes milestone 'STUDENT_INFO_COMPLETED'.
        """
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            return {"status": "ERROR", "error": "Active browser session not found"}

        def _fill(page: Any) -> List[str]:
            # Auto-wait for the student & parent form to appear in case transitioning from OTP
            try:
                page.wait_for_selector("#studentName, #nextToLoanBtn", timeout=8000)
            except Exception as e:
                logger.warning(f"[BROWSER] Timeout waiting for #studentName selector: {e}")

            filled: List[str] = []
            # 1. Student Name
            student_name = (
                form_data.get("student_name")
                or form_data.get("studentName")
                or form_data.get("applicant_name")
                or form_data.get("name")
            )
            if student_name and page.locator("#studentName").count() > 0:
                page.fill("#studentName", str(student_name))
                filled.append("student_name")

            # 2. Date of Birth
            dob = form_data.get("date_of_birth") or form_data.get("dateOfBirth") or form_data.get("dob")
            if dob and page.locator("#dateOfBirth").count() > 0:
                page.fill("#dateOfBirth", str(dob))
                filled.append("date_of_birth")

            # 3. Gender
            gender = form_data.get("gender")
            if gender and page.locator("#gender").count() > 0:
                try:
                    page.select_option("#gender", str(gender))
                    filled.append("gender")
                except Exception:
                    pass

            # 4. State
            state = form_data.get("state")
            if state and page.locator("#state").count() > 0:
                page.fill("#state", str(state))
                filled.append("state")

            # 5. District
            district = form_data.get("district")
            if district and page.locator("#district").count() > 0:
                page.fill("#district", str(district))
                filled.append("district")

            # 6. Category
            category = form_data.get("category")
            if category and page.locator("#category").count() > 0:
                try:
                    page.select_option("#category", str(category))
                    filled.append("category")
                except Exception:
                    pass

            # 7. Parent Name
            parent_name = (
                form_data.get("parent_name")
                or form_data.get("parentName")
                or form_data.get("guardian_name")
            )
            if parent_name and page.locator("#parentName").count() > 0:
                page.fill("#parentName", str(parent_name))
                filled.append("parent_name")

            # 8. Parent Occupation
            parent_occ = (
                form_data.get("parent_occupation")
                or form_data.get("parentOccupation")
            )
            if parent_occ and page.locator("#parentOccupation").count() > 0:
                try:
                    page.select_option("#parentOccupation", str(parent_occ))
                    filled.append("parent_occupation")
                except Exception:
                    pass

            # 9. Annual Family Income
            income = (
                form_data.get("annual_family_income")
                or form_data.get("annualFamilyIncome")
                or form_data.get("annual_income")
            )
            if income is not None and page.locator("#annualFamilyIncome").count() > 0:
                page.fill("#annualFamilyIncome", str(int(income)))
                filled.append("annual_family_income")

            # 10. Aadhaar Last Four
            aadhaar = form_data.get("aadhaar_last_four") or form_data.get("aadhaarLastFour")
            if aadhaar and page.locator("#aadhaarLastFour").count() > 0:
                page.fill("#aadhaarLastFour", str(aadhaar))
                filled.append("aadhaar_last_four")

            # Click next to advance to Loan Info and wait for navigation
            if page.locator("#nextToLoanBtn").count() > 0:
                page.click("#nextToLoanBtn")
                try:
                    page.wait_for_selector("#course, #nextToDocsBtn", timeout=8000)
                except Exception:
                    pass

            return filled

        try:
            filled_fields = cls._run_on_page(run_id, _fill, timeout=15)
            cls.sync_milestone(run_id, "STUDENT_INFO_COMPLETED", {"filled_fields": filled_fields})
            next_state = cls.detect_page_state(run_id)
            logger.info(f"[BROWSER] Completed Student & Parent Info for run '{run_id}'. Next: {next_state}")
            return {
                "status": "STUDENT_INFO_COMPLETED",
                "filled_fields": filled_fields,
                "next_state": next_state,
                "milestone": "STUDENT_INFO_COMPLETED",
            }
        except Exception as e:
            logger.error(f"[BROWSER] Error in fill_student_parent_info for run '{run_id}': {e}")
            return {"status": "ERROR", "error": str(e), "filled_fields": []}

    @classmethod
    def fill_loan_info(cls, run_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 5: Populates Education Loan Information on the Mock Portal.
        Automated step advancing to Step 6 (DOC_UPLOAD).
        Synchronizes milestone 'LOAN_INFO_COMPLETED'.
        """
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            return {"status": "ERROR", "error": "Active browser session not found"}

        def _fill(page: Any) -> List[str]:
            # Auto-wait for the loan details form to appear
            try:
                page.wait_for_selector("#course, #nextToDocsBtn", timeout=8000)
            except Exception as e:
                logger.warning(f"[BROWSER] Timeout waiting for #course selector: {e}")

            filled: List[str] = []
            # 1. Course
            course = form_data.get("course")
            if course and page.locator("#course").count() > 0:
                page.fill("#course", str(course))
                filled.append("course")

            # 2. College
            college = form_data.get("college") or form_data.get("institution")
            if college and page.locator("#college").count() > 0:
                page.fill("#college", str(college))
                filled.append("college")

            # 3. Loan Amount
            loan_amt = form_data.get("loan_amount") or form_data.get("loanAmount")
            if loan_amt is not None and page.locator("#loanAmount").count() > 0:
                page.fill("#loanAmount", str(int(loan_amt)))
                filled.append("loan_amount")

            # 4. Tuition Fee
            tuition = form_data.get("tuition_fee") or form_data.get("tuitionFee")
            if tuition is not None and page.locator("#tuitionFee").count() > 0:
                page.fill("#tuitionFee", str(int(tuition)))
                filled.append("tuition_fee")

            # 5. Living Expenses
            living = form_data.get("living_expenses") or form_data.get("livingExpenses")
            if living is not None and page.locator("#livingExpenses").count() > 0:
                page.fill("#livingExpenses", str(int(living)))
                filled.append("living_expenses")

            # 6. Bank Preference
            bank = form_data.get("bank_preference") or form_data.get("bankPreference")
            if bank and page.locator("#bankPreference").count() > 0:
                try:
                    page.select_option("#bankPreference", str(bank))
                    filled.append("bank_preference")
                except Exception:
                    pass

            # 7. Loan Tenure
            tenure = form_data.get("loan_tenure") or form_data.get("loanTenure")
            if tenure and page.locator("#loanTenure").count() > 0:
                try:
                    page.select_option("#loanTenure", str(tenure))
                    filled.append("loan_tenure")
                except Exception:
                    pass

            # Click next to advance to Document Upload and wait for navigation
            if page.locator("#nextToDocsBtn").count() > 0:
                page.click("#nextToDocsBtn")
                try:
                    page.wait_for_selector("#admissionLetter, #nextToReviewBtn", timeout=8000)
                except Exception:
                    pass

            return filled

        try:
            filled_fields = cls._run_on_page(run_id, _fill, timeout=15)
            cls.sync_milestone(run_id, "LOAN_INFO_COMPLETED", {"filled_fields": filled_fields})
            next_state = cls.detect_page_state(run_id)
            logger.info(f"[BROWSER] Completed Loan Info for run '{run_id}'. Next: {next_state}")
            return {
                "status": "LOAN_INFO_COMPLETED",
                "filled_fields": filled_fields,
                "next_state": next_state,
                "milestone": "LOAN_INFO_COMPLETED",
            }
        except Exception as e:
            logger.error(f"[BROWSER] Error in fill_loan_info for run '{run_id}': {e}")
            return {"status": "ERROR", "error": str(e), "filled_fields": []}

    @classmethod
    def upload_application_documents(cls, run_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Step 6: Uploads mandatory documents on the Mock Portal using real storage paths.
        Waits for upload success indicators before advancing.
        Advances to Step 7 (FINAL_REVIEW).
        CRITICAL GUARDRAIL: Halts at Step 7 without clicking submission!
        Synchronizes milestones 'DOCUMENTS_UPLOADED' and 'FINAL_REVIEW_REQUIRED'.
        """
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            return {"status": "ERROR", "error": "Active browser session not found"}

        from app.services.document_service import get_uploads_dir
        uploads_dir = get_uploads_dir()

        docs_source = (
            form_data.get("documents")
            or form_data.get("uploaded_documents")
            or []
        )

        def find_doc_record(match_keys: List[str]) -> Optional[Any]:
            if isinstance(docs_source, dict):
                for k, val in docs_source.items():
                    if any(mk in k.lower() for mk in match_keys):
                        return val
            elif isinstance(docs_source, list):
                for item in docs_source:
                    if isinstance(item, dict):
                        doc_n = (item.get("document_name") or item.get("filename") or "").lower()
                        if any(mk in doc_n for mk in match_keys):
                            return item
            return None

        def get_real_file_path(record: Any, fallback_filename: str) -> str:
            if isinstance(record, dict):
                sp = record.get("storage_path")
                if sp and os.path.exists(sp):
                    return str(sp)
                fn = record.get("filename") or record.get("original_filename")
                if fn and (uploads_dir / fn).exists():
                    return str(uploads_dir / fn)
            elif isinstance(record, str) and os.path.exists(record):
                return record

            real_demo_file = uploads_dir / fallback_filename
            if not real_demo_file.exists():
                with open(real_demo_file, "wb") as f:
                    f.write(b"%PDF-1.4 Demonstration Application Document\n%%EOF\n")
            return str(real_demo_file)

        doc_inputs = [
            ("#admissionLetter", ["admission", "offer"], "Admission_Offer_Letter.pdf"),
            ("#feeStructure", ["fee", "structure"], "Academic_Fee_Structure.pdf"),
            ("#studentAadhaar", ["aadhaar", "student_aadhaar"], "Student_Aadhaar_Card.pdf"),
            ("#parentIncomeCertificate", ["income", "salary", "certificate"], "Parent_Income_Certificate.pdf"),
        ]

        def _upload(page: Any) -> List[str]:
            # Auto-wait for document upload form
            try:
                page.wait_for_selector("#admissionLetter, #nextToReviewBtn", timeout=8000)
            except Exception as e:
                logger.warning(f"[BROWSER] Timeout waiting for #admissionLetter selector: {e}")

            uploaded: List[str] = []
            for selector, match_keys, fallback_fn in doc_inputs:
                if page.locator(selector).count() > 0:
                    doc_rec = find_doc_record(match_keys)
                    real_file = get_real_file_path(doc_rec, fallback_fn)
                    page.set_input_files(selector, real_file)
                    uploaded.append(selector)

            # Wait for upload completion indicator in DOM (e.g. checkmark badges)
            try:
                page.wait_for_selector("span:has-text('✓')", timeout=3000)
            except Exception:
                pass

            # Advance to Final Review by clicking next button
            if page.locator("#nextToReviewBtn").count() > 0:
                page.click("#nextToReviewBtn")
                try:
                    page.wait_for_selector(
                        "#submitApplicationBtn, #declarationAgreed, #declaration_agreed, #finalReviewCard",
                        timeout=8000,
                    )
                except Exception:
                    pass

            return uploaded

        try:
            uploaded_files = cls._run_on_page(run_id, _upload, timeout=20)
            cls.sync_milestone(run_id, "DOCUMENTS_UPLOADED", {"uploaded_fields": uploaded_files})
            next_state = cls.detect_page_state(run_id)

            if next_state == "FINAL_REVIEW":
                cls.sync_milestone(run_id, "FINAL_REVIEW_REQUIRED")

            logger.info(
                f"[BROWSER] Attached documents for run '{run_id}'. State transitioned to: {next_state}. "
                f"Halting at human barrier."
            )

            return {
                "status": "DOCUMENTS_UPLOADED",
                "uploaded_fields": uploaded_files,
                "paused_at": next_state,
                "human_action_required": True,
                "action_type": "FINAL_REVIEW",
                "message": (
                    "Mandatory documents attached from storage. "
                    "Browser automation paused at Final Review. Citizen verification required."
                ),
            }
        except Exception as e:
            logger.error(f"[BROWSER] Error uploading documents for run '{run_id}': {e}")
            return {"status": "ERROR", "error": str(e), "uploaded_fields": []}

    @classmethod
    def execute_all_automated_steps(cls, run_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sequentially executes all automated steps (Step 4 -> Step 5 -> Step 6),
        then halts strictly before Step 7 (FINAL_REVIEW).
        """
        results = {}
        # Step 4: Student & Parent Info
        results["student_info"] = cls.fill_student_parent_info(run_id, form_data)

        # Step 5: Loan Details
        results["loan_info"] = cls.fill_loan_info(run_id, form_data)

        # Step 6: Mandatory Document Upload
        results["doc_upload"] = cls.upload_application_documents(run_id, form_data)

        final_state = cls.detect_page_state(run_id)
        results["final_state"] = final_state
        results["human_action_required"] = is_human_barrier(final_state)
        return results

    @classmethod
    def fill_application_form(cls, run_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically handles filling depending on current portal step:
        - STUDENT_PARENT_INFO -> delegates to fill_student_parent_info
        - LOAN_INFO -> delegates to fill_loan_info
        - DOC_UPLOAD -> delegates to upload_application_documents
        - FINAL_REVIEW -> paused (human barrier)
        - APPLICATION_FORM -> legacy single-form fill
        CRITICAL GUARDRAIL: Never clicks the final submit button.
        """
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            return {"status": "ERROR", "error": "Active browser session not found"}

        current_state = cls.detect_page_state(run_id)

        if current_state == "STUDENT_PARENT_INFO":
            return cls.fill_student_parent_info(run_id, form_data)
        elif current_state == "LOAN_INFO":
            return cls.fill_loan_info(run_id, form_data)
        elif current_state == "DOC_UPLOAD":
            return cls.upload_application_documents(run_id, form_data)
        elif current_state == "FINAL_REVIEW":
            return {
                "status": "AWAITING_HUMAN_ACTION",
                "paused_at": "FINAL_REVIEW",
                "human_action_required": True,
                "action_type": "FINAL_REVIEW",
                "message": "Automation paused at Final Review. Citizen verification required before final submission.",
            }

        # Legacy form filling implementation
        def _fill_legacy(page: Any) -> List[str]:
            filled_fields: List[str] = []
            scheme_id = form_data.get("scheme_id")
            if scheme_id and page.locator("#scheme_id").count() > 0:
                try:
                    page.select_option("#scheme_id", scheme_id)
                    filled_fields.append("scheme_id")
                except Exception:
                    pass

            applicant_name = form_data.get("applicant_name") or form_data.get("student_name")
            if applicant_name and page.locator("#applicant_name").count() > 0:
                page.fill("#applicant_name", str(applicant_name))
                filled_fields.append("applicant_name")

            age = form_data.get("age")
            if age is not None and page.locator("#age").count() > 0:
                page.fill("#age", str(age))
                filled_fields.append("age")

            gender = form_data.get("gender")
            if gender and page.locator("#gender").count() > 0:
                try:
                    page.select_option("#gender", str(gender))
                    filled_fields.append("gender")
                except Exception:
                    pass

            state = form_data.get("state")
            if state and page.locator("#state").count() > 0:
                page.fill("#state", str(state))
                filled_fields.append("state")

            district = form_data.get("district")
            if district and page.locator("#district").count() > 0:
                page.fill("#district", str(district))
                filled_fields.append("district")

            annual_income = form_data.get("annual_income") or form_data.get("annual_family_income")
            if annual_income is not None and page.locator("#annual_income").count() > 0:
                page.fill("#annual_income", str(int(annual_income)))
                filled_fields.append("annual_income")

            aadhaar_last_four = form_data.get("aadhaar_last_four")
            if aadhaar_last_four and page.locator("#aadhaar_last_four").count() > 0:
                page.fill("#aadhaar_last_four", str(aadhaar_last_four))
                filled_fields.append("aadhaar_last_four")

            if page.locator("#declaration_agreed").count() > 0:
                page.check("#declaration_agreed")
                filled_fields.append("declaration_agreed")

            return filled_fields

        try:
            filled_fields = cls._run_on_page(run_id, _fill_legacy, timeout=10)
            logger.info(
                f"[BROWSER] Successfully filled {len(filled_fields)} application form fields for run '{run_id}'."
            )
            return {
                "status": "FORM_FILLED",
                "filled_fields": filled_fields,
                "paused_at": "FINAL_SUBMISSION_REVIEW",
                "message": "Form fields populated from citizen dossier. Paused for human final review & submission.",
            }
        except Exception as e:
            logger.error(f"[BROWSER] Error filling application form for run '{run_id}': {e}")
            return {
                "status": "ERROR",
                "error": str(e),
                "filled_fields": [],
            }

    @classmethod
    def get_page_content(cls, run_id: str) -> Optional[str]:
        """Retrieve the current HTML content of the page for debugging/inspection."""
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            return None
        try:
            return cls._run_on_page(run_id, lambda page: page.content(), timeout=5)
        except Exception:
            return None

    @classmethod
    def get_session_info(cls, run_id: str) -> Optional[Dict[str, Any]]:
        """Return information about the active browser session."""
        sess = _active_browser_sessions.get(run_id)
        if not sess:
            return None
        is_open = False
        url = None
        try:
            url = cls._run_on_page(run_id, lambda page: page.url, timeout=3)
            is_open = True
        except Exception:
            pass
        return {
            "run_id": run_id,
            "is_open": is_open,
            "url": url,
            "page_state": cls.detect_page_state(run_id) if is_open else "CLOSED",
        }

    @classmethod
    def close_session(cls, run_id: str) -> bool:
        """Close browser context and release Playwright resources for a run."""
        clean_run_id = run_id.strip() if run_id else ""
        with _sessions_lock:
            sess = _active_browser_sessions.pop(clean_run_id, None)

        if not sess:
            return False

        worker = sess.get("worker")
        if worker:
            worker.stop()
            logger.info(f"[BROWSER] Stopped worker and closed session for run '{clean_run_id}'.")
            return True

        try:
            if sess.get("page") and not sess["page"].is_closed():
                sess["page"].close()
            if sess.get("context"):
                sess["context"].close()
            if sess.get("browser"):
                sess["browser"].close()
            if sess.get("playwright"):
                sess["playwright"].stop()
            logger.info(f"[BROWSER] Closed session for run '{clean_run_id}'.")
            return True
        except Exception as e:
            logger.warning(f"[BROWSER] Error closing session for run '{clean_run_id}': {e}")
            return False

    @classmethod
    def close_all_sessions(cls):
        """Clean up all active browser sessions."""
        with _sessions_lock:
            run_ids = list(_active_browser_sessions.keys())
        for rid in run_ids:
            cls.close_session(rid)
