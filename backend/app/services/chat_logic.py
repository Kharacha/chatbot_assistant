from typing import List
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Business, Chunk, Conversation, Message
from .embeddings import get_single_embedding
from ..config import settings
from openai import OpenAI

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def cosine_sim(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    if matrix.shape[0] == 0:
        return np.array([])
    q = query_vec / (np.linalg.norm(query_vec) + 1e-8)
    m = matrix / (np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-8)
    return m @ q


def get_or_create_business(db: Session, business_id: str, base_url: str | None = None) -> Business:
    stmt = select(Business).where(Business.business_id == business_id)
    biz = db.scalar(stmt)
    if biz:
        if base_url and not biz.base_url:
            biz.base_url = base_url
            db.commit()
        return biz

    biz = Business(business_id=business_id, base_url=base_url)
    db.add(biz)
    db.commit()
    db.refresh(biz)
    return biz


def create_conversation(db: Session, biz: Business, user_session_id: str | None) -> Conversation:
    conv = Conversation(business_id=biz.id, user_session_id=user_session_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def get_or_create_conversation(
    db: Session, biz: Business, user_session_id: str | None
) -> Conversation:
    if not user_session_id:
        return create_conversation(db, biz, None)

    stmt = (
        select(Conversation)
        .where(
            Conversation.business_id == biz.id,
            Conversation.user_session_id == user_session_id,
        )
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    conv = db.scalar(stmt)
    if conv:
        return conv
    return create_conversation(db, biz, user_session_id)


def fetch_business_chunks(db: Session, biz: Business) -> tuple[np.ndarray, List[str]]:
    stmt = select(Chunk).where(Chunk.business_id == biz.id)
    rows = db.scalars(stmt).all()
    if not rows:
        return np.zeros((0, 1536), dtype=np.float32), []

    embeddings = np.vstack([np.array(row.embedding, dtype=np.float32) for row in rows])
    texts = [row.chunk_text for row in rows]
    return embeddings, texts


def build_system_prompt(business_id: str) -> str:
    return f"""
You are a helpful assistant for a website tied to business id '{business_id}'.
Use ONLY the provided context. If the answer is not in the context, say
you are not sure and suggest contacting the business directly.

Be concise, friendly, and avoid making up facts.
"""


def call_llm(system_prompt: str, context: str, user_message: str, history: list[dict]) -> str:
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nUser question: {user_message}",
        }
    )

    completion = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=messages,
        temperature=0.4,
    )
    return completion.choices[0].message.content.strip()
