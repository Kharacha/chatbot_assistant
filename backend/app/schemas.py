from typing import List, Dict, Optional
from pydantic import BaseModel, HttpUrl


class IngestRequest(BaseModel):
    business_id: str
    texts: List[str]


class CrawlRequest(BaseModel):
    business_id: str
    base_url: HttpUrl
    max_pages: int = 20


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
    user_session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
