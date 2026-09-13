import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.scheme_discovery_service import discover_schemes
from app.services import profile_service

client = TestClient(app)


def test_scenario_1_female_maternal_scheme_included_for_eligible_female():
    """
    Scenario 1A: A female user of maternal age (e.g. 28) sees NHM Maternal Health Care (SCH-HLT-002),
    while a male user of the same age does NOT see it.
    """
    # Female age 28 in Andhra Pradesh
    female_results = discover_schemes(state="Andhra Pradesh", sector="health", age=28, gender="Female")
    female_ids = [s.scheme_id for s in female_results]

    assert "SCH-HLT-002" in female_ids, "Eligible female should see Maternal Health Care (SCH-HLT-002)"
    assert "SCH-HLT-001" in female_ids, "Universal scheme should be visible"

    # Male age 28 in Andhra Pradesh
    male_results = discover_schemes(state="Andhra Pradesh", sector="health", age=28, gender="Male")
    male_ids = [s.scheme_id for s in male_results]

    assert "SCH-HLT-002" not in male_ids, "Male applicant must NOT see female-restricted maternal scheme"
    assert "SCH-HLT-001" in male_ids, "Universal scheme must still be visible to male applicant"


def test_scenario_1_female_out_of_age_range_excluded():
    """
    Scenario 1B: A female user outside maternal age range (e.g. 55) does NOT see SCH-HLT-002 (age 18-49).
    """
    senior_female = discover_schemes(state="Andhra Pradesh", sector="health", age=55, gender="Female")
    senior_female_ids = [s.scheme_id for s in senior_female]

    assert "SCH-HLT-002" not in senior_female_ids, "Female aged 55 is outside age range (18-49) for SCH-HLT-002"


def test_scenario_2_senior_citizen_scheme_filtering():
    """
    Scenario 2: A senior citizen (age 65) sees SCH-HLT-011 (age 60+),
    whereas a young citizen (age 30) does NOT see it.
    """
    # Senior citizen age 65
    senior_results = discover_schemes(state="Maharashtra", sector="health", age=65, gender="Male")
    senior_ids = [s.scheme_id for s in senior_results]

    assert "SCH-HLT-011" in senior_ids, "Senior citizen (age 65) should see senior healthcare scheme (SCH-HLT-011)"

    # Younger citizen age 30
    young_results = discover_schemes(state="Maharashtra", sector="health", age=30, gender="Male")
    young_ids = [s.scheme_id for s in young_results]

    assert "SCH-HLT-011" not in young_ids, "Citizen age 30 must NOT see senior citizen healthcare scheme (SCH-HLT-011)"


def test_scenario_3_student_education_loan_age_window():
    """
    Scenario 3: Universal education loan access (Phase 10):
    National Student Education Loan (SCH-EDU-001) has general access (age 0-120),
    so both student (age 21) and adult learner/parent (age 40) see it.
    """
    # Student age 21
    student_results = discover_schemes(state="Karnataka", sector="education", age=21, gender="Any")
    student_ids = [s.scheme_id for s in student_results]

    assert "SCH-EDU-001" in student_ids, "Student age 21 must see National Student Education Loan (SCH-EDU-001)"

    # Applicant age 40
    older_results = discover_schemes(state="Karnataka", sector="education", age=40, gender="Any")
    older_ids = [s.scheme_id for s in older_results]

    assert "SCH-EDU-001" in older_ids, "Applicant age 40 sees National Student Education Loan under Phase 10 universal access (0-120)"


def test_scenario_4_adolescent_female_scheme():
    """
    Scenario 4: Adolescent girls scheme SCH-HLT-012 (female, age 10-19).
    - Visible to 15-year-old girl
    - Invisible to 15-year-old boy
    - Invisible to 25-year-old woman
    """
    girl_15 = discover_schemes(state="Delhi", sector="health", age=15, gender="Female")
    boy_15 = discover_schemes(state="Delhi", sector="health", age=15, gender="Male")
    woman_25 = discover_schemes(state="Delhi", sector="health", age=25, gender="Female")

    assert "SCH-HLT-012" in [s.scheme_id for s in girl_15]
    assert "SCH-HLT-012" not in [s.scheme_id for s in boy_15]
    assert "SCH-HLT-012" not in [s.scheme_id for s in woman_25]


def test_api_discover_endpoint_derives_demographics_from_profile():
    """
    Scenario 5: Full API integration — creating a female profile of age 26,
    then calling GET /api/schemes/discover?state=Andhra%20Pradesh automatically excludes
    male-only/senior schemes and includes female maternal schemes.
    """
    profile_service.clear_profiles_for_testing()

    # Create profile for the mock test user
    from app.schemas.citizen_profile_schema import CitizenProfileCreate
    profile_service.create_profile(
        CitizenProfileCreate(
            name="Lakshmi Priya",
            age=26,
            gender="Female",
            state="Andhra Pradesh",
            district="Guntur",
        ),
        user_id="test-user-system-id",
    )

    # Call API without explicit age/gender query params
    response = client.get("/api/schemes/discover?state=Andhra%20Pradesh&sector=health")
    assert response.status_code == 200
    schemes = response.json()
    scheme_ids = [s["scheme_id"] for s in schemes]

    # Female age 26 should see SCH-HLT-002 (maternal), but NOT SCH-HLT-011 (senior 60+)
    assert "SCH-HLT-002" in scheme_ids
    assert "SCH-HLT-011" not in scheme_ids
    assert "SCH-HLT-001" in scheme_ids  # universal
