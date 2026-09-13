from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import END, StateGraph
from app.agents.knowledge_agent.prompts import KNOWLEDGE_AGENT_SYSTEM_PROMPT
from app.core.config import settings
from app.services.pmkisan_action_router import detect_pmkisan_action
from app.services.rag_retrieval_service import retrieve_context


class AgentState(TypedDict):
    question: str
    state: Optional[str]
    sector: Optional[str]
    scheme_id: Optional[str]
    retrieved_chunks: List[Dict[str, Any]]
    answer: str
    sources: List[Dict[str, str]]
    grounded: bool
    action: Optional[str]
    action_url: Optional[str]
    action_title: Optional[str]
    requires_human_verification: Optional[bool]


def retrieve_node(state: AgentState) -> Dict[str, Any]:
    question = state["question"]
    target_state = state.get("state")
    target_sector = state.get("sector")
    target_scheme_id = state.get("scheme_id")

    # If scheme_id is not given, prioritize specific schemes based on question intent
    q_lower = question.lower()
    if not target_scheme_id and ("pm-kisan" in q_lower or "pm kisan" in q_lower or "pmkisan" in q_lower):
        target_scheme_id = "PM-KISAN"
    elif not target_scheme_id and any(
        kw in q_lower
        for kw in [
            "education loan",
            "student loan",
            "vidya lakshmi",
            "vidyalakshmi",
            "sch-edu-001",
            "student education",
        ]
    ):
        target_scheme_id = "SCH-EDU-001"
        target_sector = "education"

    if target_scheme_id == "SCH-EDU-001":
        target_sector = "education"

    chunks = retrieve_context(
        query=question,
        state=target_state,
        sector=target_sector,
        scheme_id=target_scheme_id,
        top_k=4,
    )
    return {"retrieved_chunks": chunks, "scheme_id": target_scheme_id}


def _call_ollama_llm(prompt: str) -> str:
    """
    Calls the Ollama local LLM API (/api/generate).
    Raises RuntimeError with a clear, actionable message if Ollama is unreachable.
    """
    import httpx

    url = f"{settings.OLLAMA_BASE_URL}/api/generate"
    try:
        response = httpx.post(
            url,
            json={
                "model": settings.LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0},
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()

    except httpx.ConnectError:
        raise RuntimeError(
            f"Cannot reach Ollama at {settings.OLLAMA_BASE_URL} — "
            "is `ollama serve` running and is the LLM model pulled? "
            f"(Run: ollama pull {settings.LLM_MODEL})"
        )
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama LLM request failed with HTTP {exc.response.status_code}: "
            f"{exc.response.text}"
        )


def generate_node(state: AgentState) -> Dict[str, Any]:
    question = state["question"]
    chunks = state.get("retrieved_chunks", [])
    target_scheme_id = state.get("scheme_id")

    # Detect actionable PM-KISAN intent
    action_route = detect_pmkisan_action(
        question=question,
        retrieved_chunks=chunks,
        explicit_scheme_id=target_scheme_id,
    )

    if not chunks:
        # If no chunks but an actionable intent was recognized, return guided route
        if action_route:
            return {
                "answer": (
                    f"To complete {action_route['action_title']}, please proceed to the official PM-KISAN portal page. "
                    "You will need your Aadhaar number or Registration Number, and will need to complete CAPTCHA / OTP verification."
                ),
                "sources": [
                    {
                        "scheme_id": "PM-KISAN",
                        "scheme_name": "PM-KISAN",
                        "level": "central",
                    }
                ],
                "grounded": True,
                "scheme_id": action_route["scheme_id"],
                "action": action_route["action"],
                "action_url": action_route["action_url"],
                "action_title": action_route["action_title"],
                "requires_human_verification": action_route["requires_human_verification"],
            }

        return {
            "answer": "I don't have information on that in the current scheme data.",
            "sources": [],
            "grounded": False,
            "scheme_id": None,
            "action": None,
            "action_url": None,
            "action_title": None,
            "requires_human_verification": False,
        }

    # Deduplicated source metadata
    seen_ids: set = set()
    sources: List[Dict[str, str]] = []
    for c in chunks:
        meta = c["metadata"]
        sid = meta.get("scheme_id", "")
        if sid and sid not in seen_ids:
            seen_ids.add(sid)
            sources.append({
                "scheme_id": sid,
                "scheme_name": meta.get("scheme_name", "Unknown Scheme"),
                "level": meta.get("level", "central"),
            })

    # Build context string from retrieved chunks
    context_blocks = [f"--- Chunk {i} ---\n{c['text']}" for i, c in enumerate(chunks, 1)]
    context_text = "\n\n".join(context_blocks)

    prompt = KNOWLEDGE_AGENT_SYSTEM_PROMPT.format(
        context=context_text, question=question
    )

    # Call Ollama LLM via provider-agnostic wrapper
    if settings.LLM_PROVIDER == "ollama":
        answer_text = _call_ollama_llm(prompt)
    else:
        raise ValueError(f"Unsupported LLM provider: '{settings.LLM_PROVIDER}'")

    is_ungrounded = (
        "don't have information" in answer_text.lower()
        or "not available in the current" in answer_text.lower()
    )

    matched_scheme_id = None
    if action_route:
        matched_scheme_id = action_route["scheme_id"]
    elif target_scheme_id:
        matched_scheme_id = target_scheme_id
    elif sources:
        matched_scheme_id = sources[0]["scheme_id"]

    return {
        "answer": answer_text,
        "sources": [] if is_ungrounded else sources,
        "grounded": not is_ungrounded,
        "scheme_id": matched_scheme_id,
        "action": action_route["action"] if action_route else None,
        "action_url": action_route["action_url"] if action_route else None,
        "action_title": action_route["action_title"] if action_route else None,
        "requires_human_verification": action_route["requires_human_verification"] if action_route else False,
    }


def build_knowledge_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("generate", generate_node)
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()


knowledge_agent_graph = build_knowledge_agent_graph()


def run_knowledge_agent(
    question: str,
    state: Optional[str] = None,
    sector: Optional[str] = None,
    scheme_id: Optional[str] = None,
) -> Dict[str, Any]:
    initial_state: AgentState = {
        "question": question,
        "state": state,
        "sector": sector,
        "scheme_id": scheme_id,
        "retrieved_chunks": [],
        "answer": "",
        "sources": [],
        "grounded": False,
        "action": None,
        "action_url": None,
        "action_title": None,
        "requires_human_verification": False,
    }
    result = knowledge_agent_graph.invoke(initial_state)
    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "grounded": result["grounded"],
        "scheme_id": result.get("scheme_id"),
        "action": result.get("action"),
        "action_url": result.get("action_url"),
        "action_title": result.get("action_title"),
        "requires_human_verification": result.get("requires_human_verification", False),
    }
