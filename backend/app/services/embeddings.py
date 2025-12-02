from typing import List
import numpy as np
from openai import OpenAI
from ..config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)


def get_embeddings(texts: List[str]) -> np.ndarray:
    """
    Return np.ndarray of shape (len(texts), dim).
    """
    if not texts:
        return np.zeros((0, 1536), dtype=np.float32)

    resp = client.embeddings.create(
        model=settings.OPENAI_EMBED_MODEL,
        input=texts,
    )
    vectors = [np.array(d.embedding, dtype=np.float32) for d in resp.data]
    return np.vstack(vectors)


def get_single_embedding(text: str) -> np.ndarray:
    return get_embeddings([text])[0]
