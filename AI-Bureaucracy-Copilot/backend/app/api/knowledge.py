from fastapi import APIRouter, Depends, HTTPException, status
from app.agents.knowledge_agent.graph import run_knowledge_agent
from app.core.dependencies import get_current_user
from app.db.models import User
from app.rag.vector_store import VectorStore
from app.schemas.knowledge_schema import KnowledgeAskRequest, KnowledgeAskResponse

router = APIRouter()


@router.post(
    "/knowledge/ask",
    response_model=KnowledgeAskResponse,
    status_code=status.HTTP_200_OK,
)
def ask_knowledge_agent(
    payload: KnowledgeAskRequest,
    current_user: User = Depends(get_current_user),
):
    vector_store = VectorStore()
    if vector_store.count() == 0:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector index not built yet. Please run 'python -m app.scripts.build_index' first.",
        )

    try:
        result = run_knowledge_agent(
            question=payload.question,
            state=payload.state,
            sector=payload.sector,
            scheme_id=payload.scheme_id,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge Agent error: {str(exc)}",
        )
