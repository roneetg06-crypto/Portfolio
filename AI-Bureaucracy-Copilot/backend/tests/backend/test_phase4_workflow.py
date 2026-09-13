import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agents.document_agent.graph import run_document_agent
from app.services.document_service import clear_document_store_for_testing

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_stores():
    clear_document_store_for_testing()
    yield
    clear_document_store_for_testing()


def test_scenario_1_information_requirements_fetch():
    """Scenario 1: GET /api/schemes/{scheme_id}/information-requirements returns required fields."""
    response = client.get("/api/schemes/SCH-HLT-001/information-requirements")
    assert response.status_code == 200
    data = response.json()

    assert data["scheme_id"] == "SCH-HLT-001"
    assert "required_info" in data
    assert len(data["required_info"]) > 0

    field_names = [f["name"] for f in data["required_info"]]
    assert "ration_card_number" in field_names
    assert "annual_family_income" in field_names


def test_scenario_2_information_submission_and_validation():
    """Scenario 2: POST /api/schemes/{scheme_id}/information validates and stores input."""
    # Invalid submission missing required fields
    invalid_payload = {
        "profile_id": "prof-001",
        "data": {"ration_card_number": ""},
    }
    invalid_res = client.post("/api/schemes/SCH-HLT-001/information", json=invalid_payload)
    assert invalid_res.status_code == 422
    assert "error" in invalid_res.json()

    # Valid submission
    valid_payload = {
        "profile_id": "prof-001",
        "data": {
            "ration_card_number": "123456789012",
            "annual_family_income": 150000,
            "has_pre_existing_condition": False,
        },
    }
    valid_res = client.post("/api/schemes/SCH-HLT-001/information", json=valid_payload)
    assert valid_res.status_code == 200
    res_data = valid_res.json()
    assert res_data["status"] == "saved"
    assert res_data["missing_information"] == []


def test_scenario_3_document_agent_output():
    """Scenario 3: Document Agent LangGraph node returns correct required documents."""
    # Test direct Agent call
    agent_res = run_document_agent(scheme_id="SCH-HLT-001")
    assert "required_documents" in agent_res
    doc_names = [d["name"] for d in agent_res["required_documents"]]
    assert "aadhaar_card" in doc_names
    assert "ration_card" in doc_names

    # Test API endpoint
    response = client.get("/api/schemes/SCH-HLT-001/documents/required")
    assert response.status_code == 200
    data = response.json()
    assert data["scheme_id"] == "SCH-HLT-001"
    assert len(data["required_documents"]) > 0


def test_scenario_4_document_upload_and_status():
    """Scenario 4: Valid file upload processes and assigns verification status."""
    dummy_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    upload_res = client.post(
        "/api/documents/upload",
        data={
            "document_name": "aadhaar_card",
            "scheme_id": "SCH-HLT-001",
            "profile_id": "prof-001",
        },
        files={"file": ("my_aadhaar.pdf", io.BytesIO(dummy_pdf), "application/pdf")},
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    assert upload_data["verification_status"] in ("VERIFIED", "MANUAL_VERIFICATION_REQUIRED")

    # Check status endpoint
    status_res = client.get("/api/documents/status?scheme_id=SCH-HLT-001&profile_id=prof-001")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["scheme_id"] == "SCH-HLT-001"

    docs = {d["name"]: d for d in status_data["documents"]}
    assert "aadhaar_card" in docs
    assert docs["aadhaar_card"]["status"] in ("VERIFIED", "MANUAL_VERIFICATION_REQUIRED")
    assert docs["ration_card"]["status"] == "MISSING"


def test_scenario_5_invalid_file_rejection():
    """Scenario 5: Rejects unauthorized file type or oversized upload with 400 error."""
    # Test illegal extension (.exe)
    invalid_ext_res = client.post(
        "/api/documents/upload",
        data={
            "document_name": "aadhaar_card",
            "scheme_id": "SCH-HLT-001",
            "profile_id": "prof-001",
        },
        files={"file": ("malicious.exe", io.BytesIO(b"binary data"), "application/octet-stream")},
    )
    assert invalid_ext_res.status_code == 400
    assert "Unsupported file type" in invalid_ext_res.json()["error"]

    # Test oversized file (> 5MB)
    large_bytes = b"A" * (5 * 1024 * 1024 + 100)
    oversized_res = client.post(
        "/api/documents/upload",
        data={
            "document_name": "aadhaar_card",
            "scheme_id": "SCH-HLT-001",
            "profile_id": "prof-001",
        },
        files={"file": ("large_doc.pdf", io.BytesIO(large_bytes), "application/pdf")},
    )
    assert oversized_res.status_code == 400
    assert "maximum permitted limit" in oversized_res.json()["error"].lower() or "5mb" in oversized_res.json()["error"].lower()


def test_scenario_6_independent_tracking_multiple_documents():
    """Scenario 6: Multiple documents for same scheme are tracked independently."""
    pdf1 = b"%PDF-1.4 Aadhaar Card Document content"
    pdf2 = b"%PDF-1.4 Ration Card Document content"

    # Upload Doc 1 (Aadhaar)
    client.post(
        "/api/documents/upload",
        data={
            "document_name": "aadhaar_card",
            "scheme_id": "SCH-HLT-001",
            "profile_id": "prof-002",
        },
        files={"file": ("aadhaar.pdf", io.BytesIO(pdf1), "application/pdf")},
    )

    # Check status before Doc 2
    status_res1 = client.get("/api/documents/status?scheme_id=SCH-HLT-001&profile_id=prof-002").json()
    docs1 = {d["name"]: d for d in status_res1["documents"]}
    assert docs1["aadhaar_card"]["status"] != "MISSING"
    assert docs1["ration_card"]["status"] == "MISSING"

    # Upload Doc 2 (Ration card)
    client.post(
        "/api/documents/upload",
        data={
            "document_name": "ration_card",
            "scheme_id": "SCH-HLT-001",
            "profile_id": "prof-002",
        },
        files={"file": ("ration.pdf", io.BytesIO(pdf2), "application/pdf")},
    )

    # Check status after Doc 2
    status_res2 = client.get("/api/documents/status?scheme_id=SCH-HLT-001&profile_id=prof-002").json()
    docs2 = {d["name"]: d for d in status_res2["documents"]}
    assert docs2["aadhaar_card"]["status"] != "MISSING"
    assert docs2["ration_card"]["status"] != "MISSING"


def test_scenario_7_complete_phase4_backend_workflow():
    """Scenario 7: Full Phase 4 flow: fetch reqs -> submit info -> check required docs -> upload -> check status."""
    profile_id = "prof-e2e"
    scheme_id = "SCH-HLT-004"

    # 1. Fetch info requirements
    req_res = client.get(f"/api/schemes/{scheme_id}/information-requirements")
    assert req_res.status_code == 200

    # 2. Submit dynamic information
    info_payload = {
        "profile_id": profile_id,
        "data": {
            "white_ration_card_number": "WRC-998877",
            "patient_category": "General",
            "family_bpl_declaration": True,
        },
    }
    submit_res = client.post(f"/api/schemes/{scheme_id}/information", json=info_payload)
    assert submit_res.status_code == 200

    # 3. Get required documents from Document Agent
    agent_res = client.get(f"/api/schemes/{scheme_id}/documents/required?profile_id={profile_id}")
    assert agent_res.status_code == 200

    # 4. Upload required document
    pdf_content = b"%PDF-1.4 Doctor YSR Aarogyasri Card Document"
    upload_res = client.post(
        "/api/documents/upload",
        data={
            "document_name": "aarogyasri_card",
            "scheme_id": scheme_id,
            "profile_id": profile_id,
        },
        files={"file": ("aarogyasri.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert upload_res.status_code == 201

    # 5. Check document status
    final_status = client.get(f"/api/documents/status?scheme_id={scheme_id}&profile_id={profile_id}")
    assert final_status.status_code == 200
    docs = {d["name"]: d for d in final_status.json()["documents"]}
    assert docs["aarogyasri_card"]["status"] in ("VERIFIED", "MANUAL_VERIFICATION_REQUIRED")
