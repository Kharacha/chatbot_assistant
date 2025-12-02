from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas import CrawlRequest, IngestRequest
from ..services.crawl import crawl_website
from ..services.embeddings import get_embeddings
from ..models import Business, Page, Chunk
from ..services.chat_logic import get_or_create_business

router = APIRouter(prefix="/crawl", tags=["crawl"])


@router.post("/crawl_and_ingest")
def crawl_and_ingest(req: CrawlRequest, db: Session = Depends(get_db)):
    # Get or create business
    biz: Business = get_or_create_business(db, req.business_id, str(req.base_url))

    chunks, page_urls = crawl_website(str(req.base_url), max_pages=req.max_pages)
    if not chunks:
        raise HTTPException(status_code=400, detail="No text content extracted.")

    embeddings = get_embeddings(chunks)

    # Clear old chunks for this business (simple but effective for MVP)
    db.query(Chunk).filter(Chunk.business_id == biz.id).delete()
    db.query(Page).filter(Page.business_id == biz.id).delete()
    db.commit()

    # Create pages
    url_to_page: dict[str, Page] = {}
    for url in page_urls:
        page = Page(business_id=biz.id, url=url, status="crawled")
        db.add(page)
        db.flush()
        url_to_page[url] = page

    # For simplicity, we don't track which chunk came from which page URL here.
    # Could be improved by returning (chunks, mapping) from crawl_website.
    for i, text in enumerate(chunks):
        emb = embeddings[i].tolist()
        chunk = Chunk(
            business_id=biz.id,
            page_id=None,
            chunk_text=text,
            embedding=emb,
        )
        db.add(chunk)

    db.commit()

    return {
        "business_id": req.business_id,
        "base_url": str(req.base_url),
        "chunks": len(chunks),
        "pages_discovered": len(page_urls),
        "message": "Crawled and ingested successfully.",
    }


@router.post("/ingest_raw")
def ingest_raw(req: IngestRequest, db: Session = Depends(get_db)):
    biz = get_or_create_business(db, req.business_id, None)
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts cannot be empty")

    embeddings = get_embeddings(req.texts)

    db.query(Chunk).filter(Chunk.business_id == biz.id).delete()
    db.commit()

    for i, text in enumerate(req.texts):
        emb = embeddings[i].tolist()
        chunk = Chunk(business_id=biz.id, page_id=None, chunk_text=text, embedding=emb)
        db.add(chunk)

    db.commit()

    return {
        "business_id": req.business_id,
        "chunks": len(req.texts),
        "message": "Ingested raw text successfully.",
    }
