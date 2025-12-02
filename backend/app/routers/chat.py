from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import numpy as np
from ..db import get_db
from ..schemas import ChatRequest, ChatResponse
from ..services.chat_logic import (
    get_or_create_business,
    fetch_business_chunks,
    build_system_prompt,
    call_llm,
    cosine_sim,
    get_or_create_conversation,
)
from ..models import Business, Conversation, Message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{business_id}", response_model=ChatResponse)
def chat(
    business_id: str,
    req: ChatRequest,
    db: Session = Depends(get_db),
):
    biz = get_or_create_business(db, business_id)
    embeddings, texts = fetch_business_chunks(db, biz)

    if embeddings.shape[0] == 0:
        raise HTTPException(
            status_code=400,
            detail="No content indexed for this business. Crawl or ingest first.",
        )

    query_emb = np.array([], dtype=np.float32)
    try:
        from ..services.embeddings import get_single_embedding

        query_emb = get_single_embedding(req.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Embedding error") from e

    sims = cosine_sim(query_emb, embeddings)

    top_k = min(5, sims.shape[0])
    top_idx = np.argsort(-sims)[:top_k]
    top_chunks = [texts[i] for i in top_idx]
    context = "\n\n---\n\n".join(top_chunks)

    system_prompt = build_system_prompt(business_id)

    history = []
    if req.history:
        for m in req.history:
            if m.role in {"user", "assistant", "system"} and m.content.strip():
                history.append({"role": m.role, "content": m.content})

    answer = call_llm(system_prompt, context, req.message, history)

    # Store conversation + messages (simple version)
    conv: Conversation = get_or_create_conversation(db, biz, req.user_session_id)

    db.add(Message(conversation_id=conv.id, role="user", content=req.message))
    db.add(Message(conversation_id=conv.id, role="assistant", content=answer))
    db.commit()

    return ChatResponse(reply=answer)
