from typing import List, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from ..config import settings


def is_same_domain(base_url: str, target_url: str) -> bool:
    base = urlparse(base_url)
    target = urlparse(target_url)
    # allow relative URLs (empty netloc) and same host
    return target.netloc == "" or target.netloc == base.netloc


def extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Strip scripts & styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    chunks: list[str] = []

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        text = tag.get_text(separator=" ", strip=True)
        if text and len(text.split()) > 3:
            chunks.append(text)

    return "\n".join(chunks)


def chunk_text(text: str, max_chars: int = 800) -> List[str]:
    if not text:
        return []

    parts = text.split("\n")
    chunks: list[str] = []
    current = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if len(current) + len(part) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
            current = part
        else:
            current = f"{current} {part}" if current else part

    if current:
        chunks.append(current.strip())
    return chunks


def crawl_website(base_url: str, max_pages: int = 20) -> Tuple[List[str], List[str]]:
    """
    Returns (chunks, page_urls)
    """
    visited: set[str] = set()
    to_visit: list[str] = [base_url]
    collected_chunks: list[str] = []
    page_urls: list[str] = []

    session = requests.Session()
    session.headers.update({"User-Agent": settings.CRAWLER_USER_AGENT})

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        url = url.split("#")[0]
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = session.get(url, timeout=10)
        except Exception:
            continue

        if resp.status_code != 200:
            continue

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            continue

        html = resp.text
        page_text = extract_text_from_html(html)
        chunks = chunk_text(page_text)

        if chunks:
            collected_chunks.extend(chunks)
            page_urls.append(url)

        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full_url = urljoin(url, href)

            if not is_same_domain(base_url, full_url):
                continue
            if full_url in visited or full_url in to_visit:
                continue

            to_visit.append(full_url)

    return collected_chunks, page_urls
