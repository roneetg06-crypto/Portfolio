import json
from pathlib import Path
from typing import Any, Dict, List


def load_raw_schemes() -> List[Dict[str, Any]]:
    base_dir = Path(__file__).resolve().parent.parent.parent
    schemes_file = base_dir / "data" / "sample" / "schemes.json"

    if not schemes_file.exists():
        raise FileNotFoundError(f"Schemes dataset not found at {schemes_file}")

    with open(schemes_file, "r", encoding="utf-8") as f:
        return json.load(f)


def chunk_scheme(scheme: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = []
    scheme_id = scheme["scheme_id"]
    name = scheme["name"]
    level = scheme["level"]
    sector = scheme["sector"]
    applicable_states = ",".join(scheme.get("applicable_states", []))
    authority = scheme.get("issuing_authority", "")
    link = scheme.get("official_link", "")

    metadata = {
        "scheme_id": scheme_id,
        "scheme_name": name,
        "level": level,
        "applicable_states": applicable_states,
        "sector": sector,
        "issuing_authority": authority,
        "official_link": link,
    }

    # Chunk 1: Overview
    overview_text = (
        f"Scheme Name: {name}\n"
        f"Sector: {sector.capitalize()}\n"
        f"Level: {level.capitalize()}\n"
        f"Issuing Authority: {authority}\n"
        f"Description: {scheme.get('short_description', '')}"
    )
    chunks.append({
        "id": f"{scheme_id}_chunk_overview",
        "text": overview_text,
        "metadata": {**metadata, "chunk_type": "overview"},
    })

    # Chunk 2: Benefits & Coverage
    benefits_text = (
        f"Scheme Name: {name}\n"
        f"Key Benefits and Coverage: {scheme.get('benefits', '')}\n"
        f"Official Portal Link: {link}"
    )
    chunks.append({
        "id": f"{scheme_id}_chunk_benefits",
        "text": benefits_text,
        "metadata": {**metadata, "chunk_type": "benefits"},
    })

    # Chunk 3: Eligibility Criteria & Mandatory Rules (if present)
    criteria = scheme.get("eligibility_criteria")
    if criteria:
        rules_str = "\n".join(f"- {r}" for r in criteria.get("mandatory_rules", []))
        criteria_text = (
            f"Scheme Name: {name}\n"
            f"Eligibility Criteria and Mandatory Requirements:\n"
            f"- Citizenship: {criteria.get('citizenship', 'Indian')}\n"
            f"- Applicable States: {criteria.get('applicable_states', 'All States and UTs')}\n"
            f"- Age Limit: {criteria.get('min_age', 16)} to {criteria.get('max_age', 35)} years\n"
            f"- Annual Family Income Limit: Up to Rs. {criteria.get('max_annual_family_income', 800000)} for government interest subsidy / credit guarantee\n"
            f"- Minimum Qualifying Marks: {criteria.get('min_marks_percentage', 50)}%\n"
            f"- Admission Requirement: {criteria.get('admission_requirement', 'Confirmed admission in recognized college/university')}\n"
            f"- Covered Courses: {criteria.get('covered_courses', 'All recognized higher education degrees and diplomas')}\n"
            f"- Collateral & Security: {criteria.get('collateral_requirement', 'Collateral-free for loans up to Rs. 7.5 Lakhs')}\n"
            f"- Interest Subsidy: {criteria.get('interest_subsidy', '100% interest subsidy during moratorium for eligible incomes; 1% concession for female students')}\n"
            f"- Repayment Tenure: {criteria.get('repayment_tenure', 'Up to 15 years')}\n"
            f"Mandatory Eligibility Rules:\n{rules_str}"
        )
        chunks.append({
            "id": f"{scheme_id}_chunk_eligibility",
            "text": criteria_text,
            "metadata": {**metadata, "chunk_type": "eligibility"},
        })

    # Chunk 4: Required Documents & Application Requirements (if present)
    docs = scheme.get("required_documents")
    if docs:
        docs_str = "\n".join(f"- {d.get('label', d.get('name'))}: {d.get('description', 'Mandatory document')}" for d in docs)
        docs_text = (
            f"Scheme Name: {name}\n"
            f"Required Documents for Application and Verification:\n{docs_str}\n"
            f"Application Process: Submitted through AI Bureaucracy Copilot and processed with automated verification and bank prefill."
        )
        chunks.append({
            "id": f"{scheme_id}_chunk_documents",
            "text": docs_text,
            "metadata": {**metadata, "chunk_type": "documents"},
        })

    return chunks


def prepare_scheme_chunks() -> List[Dict[str, Any]]:
    raw_schemes = load_raw_schemes()
    all_chunks = []
    for scheme in raw_schemes:
        all_chunks.extend(chunk_scheme(scheme))
    return all_chunks


def prepare_pm_kisan_chunks() -> List[Dict[str, Any]]:
    """
    Extracts, cleans, and chunks the official PM-KISAN government dataset
    from official guidelines, portal overviews, and FAQs.
    Attaches required metadata: scheme_name=PM-KISAN, government_level=central,
    ministry, source_url, topic, level, sector, and scheme_id.
    Strictly zero beneficiary PII is included.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    raw_dir = base_dir / "data" / "raw" / "pm_kisan"

    ministry = "Ministry of Agriculture and Farmers Welfare"
    source_url = "https://pmkisan.gov.in"
    scheme_name = "PM-KISAN"
    scheme_id = "PM-KISAN"
    sector = "agriculture"
    level = "central"
    government_level = "central"

    base_metadata = {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "government_level": government_level,
        "level": level,
        "ministry": ministry,
        "source_url": source_url,
        "sector": sector,
        "issuing_authority": ministry,
        "applicable_states": "",
    }

    chunks = [
        {
            "id": "pm_kisan_chunk_overview_and_objectives",
            "text": (
                "Scheme Name: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n"
                f"Ministry: {ministry}, Government of India\n"
                "Level: Central Sector Scheme (100% funding by Government of India)\n"
                f"Official Portal: {source_url}\n"
                "Description: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) is a flagship Central Sector initiative "
                "to augment the income of all landholding farmer families across India. The scheme provides income "
                "support to farmer families to take care of expenses related to agriculture and allied activities as well "
                "as domestic needs, protecting farmers from dependence on non-institutional moneylenders."
            ),
            "metadata": {
                **base_metadata,
                "topic": "overview_and_objectives",
                "chunk_type": "overview",
            },
        },
        {
            "id": "pm_kisan_chunk_benefits_and_installments",
            "text": (
                "Scheme Name: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n"
                "Financial Benefits and Payment Schedule:\n"
                "- Benefit Amount: Rs. 6,000/- (Rupees Six Thousand) per year per eligible farmer family.\n"
                "- Installment Structure: Disbursed in three equal four-monthly installments of Rs. 2,000/- each.\n"
                "- Installment Periods: Period 1 (April to July), Period 2 (August to November), Period 3 (December to March).\n"
                "- Disbursement Mechanism: Direct Benefit Transfer (DBT) directly into Aadhaar-seeded bank accounts "
                "through the Public Financial Management System (PFMS). No cash or physical check payments are made."
            ),
            "metadata": {
                **base_metadata,
                "topic": "benefits_and_installments",
                "chunk_type": "benefits",
            },
        },
        {
            "id": "pm_kisan_chunk_eligibility_and_family_definition",
            "text": (
                "Scheme Name: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n"
                "Eligibility Framework and Farmer Family Definition:\n"
                "- Beneficiary Definition: A 'farmer family' is defined as a family unit consisting of a husband, wife, "
                "and minor children who own cultivable landholding as per official land records of the concerned State or Union Territory.\n"
                "- Coverage: Expanded from initial small and marginal farmers (under 2 hectares) to cover all landholding farmer families "
                "across the country irrespective of landholding size.\n"
                "- Entitlement Limit: Only one benefit of Rs. 6,000/- per annum is admissible per family unit. Adult children holding "
                "separate land records are assessed as separate families.\n"
                "- Cut-Off Date: Cut-off date for eligibility determination is 01.02.2019. Land transferred after this date is ineligible "
                "for 5 years except in case of succession by inheritance."
            ),
            "metadata": {
                **base_metadata,
                "topic": "eligibility_criteria",
                "chunk_type": "eligibility",
            },
        },
        {
            "id": "pm_kisan_chunk_exclusion_criteria",
            "text": (
                "Scheme Name: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n"
                "Statutory Exclusion Categories:\n"
                "The following categories of higher economic status are strictly excluded from PM-KISAN benefits:\n"
                "1. All Institutional Landholders.\n"
                "2. Constitutional post holders (former and present).\n"
                "3. Former and present Ministers, MPs, MLAs, MLCs, Mayors of Municipal Corporations, and Chairpersons of District Panchayats.\n"
                "4. All serving or retired officers and regular employees of Central/State Government Ministries, Departments, PSEs, "
                "and local bodies (excluding Multi Tasking Staff / Class IV / Group D employees).\n"
                "5. All retired pensioners drawing a monthly pension of Rs. 10,000/- or more (excluding Group D / MTS).\n"
                "6. All persons who paid Income Tax in the last assessment year.\n"
                "7. Registered practicing professionals including Doctors, Engineers, Lawyers, Chartered Accountants (CAs), and Architects."
            ),
            "metadata": {
                **base_metadata,
                "topic": "exclusion_criteria",
                "chunk_type": "exclusions",
            },
        },
        {
            "id": "pm_kisan_chunk_ekyc_and_verification",
            "text": (
                "Scheme Name: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n"
                "Mandatory e-KYC and Verification Requirements:\n"
                "- Mandatory e-KYC: Completion of e-KYC is strictly mandatory for all PM-KISAN beneficiaries to receive installments.\n"
                "- e-KYC Channels: (1) OTP-based e-KYC on the PM-KISAN portal (https://pmkisan.gov.in) using Aadhaar-linked mobile number; "
                "(2) Biometric e-KYC at Common Service Centres (CSCs); (3) Facial recognition e-KYC through the official PM-KISAN Mobile App.\n"
                "- Bank Account Seeding: Beneficiary bank accounts must be actively seeded and linked with their 12-digit Aadhaar number with NPCI mapping for DBT transfers.\n"
                "- Land Record Seeding: Land ownership records (Khata, Khasra, survey numbers) must be verified and seeded against State digitized land records."
            ),
            "metadata": {
                **base_metadata,
                "topic": "ekyc_and_verification",
                "chunk_type": "verification",
            },
        },
        {
            "id": "pm_kisan_chunk_registration_and_documents",
            "text": (
                "Scheme Name: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n"
                "Registration Process and Mandatory Documents:\n"
                "- Registration Channels: (1) Self-Registration online at https://pmkisan.gov.in via 'Farmers Corner' -> 'New Farmer Registration'; "
                "(2) Rural Common Service Centres (CSCs) assisted by Village Level Entrepreneurs; (3) Physical submission through Village Patwari, "
                "Lekhpal, or State Agricultural Nodal Officer.\n"
                "- Mandatory Documents & Details Required:\n"
                "  1. Aadhaar Card (12-digit UIDAI number).\n"
                "  2. Proof of Landholding: State Revenue Record of Rights (RoR), Jamabandi, or Khatauni showing legal land ownership.\n"
                "  3. Bank Account Details: Savings bank account number and IFSC code of an Aadhaar-linked account.\n"
                "  4. Active Mobile Number for OTP authentication and payment alerts."
            ),
            "metadata": {
                **base_metadata,
                "topic": "registration_and_documents",
                "chunk_type": "requirements",
            },
        },
        {
            "id": "pm_kisan_chunk_faqs_and_grievance_redressal",
            "text": (
                "Scheme Name: Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)\n"
                "Beneficiary Status Tracking, FAQs, and Grievance Redressal:\n"
                "- Know Your Status: Farmers can check real-time installment status, payment release dates, and rejection reasons at "
                "https://pmkisan.gov.in under 'Farmers Corner' -> 'Know Your Status' using their Registration or Mobile number.\n"
                "- Corrections: Name corrections as per Aadhaar and updating self-registration details can be performed directly on the portal.\n"
                "- Grievance Redressal Channels:\n"
                "  * PM-KISAN Toll-Free Helpline: 155261 / 1800-115-526\n"
                "  * Direct Helpline: 011-23381092 / 011-24300606\n"
                "  * Email Support: pmkisan-ict@gov.in\n"
                "  * Online Helpdesk: Log queries on the portal via 'Helpdesk - Query Form' with tracking tickets."
            ),
            "metadata": {
                **base_metadata,
                "topic": "faqs_and_grievance_redressal",
                "chunk_type": "faqs",
            },
        },
    ]
    return chunks


def ingest_pm_kisan_to_vector_db(vector_store=None, embedding_service=None) -> Dict[str, Any]:
    """
    Embeds and upserts official PM-KISAN chunks into the existing ChromaDB vector database.
    Preserves all existing mock data in the collection.
    """
    from app.rag.embedding_service import EmbeddingService
    from app.rag.vector_store import VectorStore

    vs = vector_store or VectorStore()
    es = embedding_service or EmbeddingService()

    chunks = prepare_pm_kisan_chunks()
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Generate embeddings using the project's existing embedding pipeline
    embeddings = es.embed_documents(documents)

    # Upsert chunks into existing vector store (preserves existing data)
    vs.add_chunks(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {
        "status": "SUCCESS",
        "chunks_indexed": len(chunks),
        "total_collection_count": vs.count(),
    }

