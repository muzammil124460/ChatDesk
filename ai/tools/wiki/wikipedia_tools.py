
import json
import re
from html import unescape
from urllib.parse import quote
import os
import tempfile
from markitdown import MarkItDown
import httpx
from langchain.tools import tool


USER_AGENT = "ChatDesk/1.0 (Wikipedia research assistant)"

LANGUAGE_CODE_PATTERN = re.compile(r"^[a-zA-Z0-9-]{2,20}$")


def json_response(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def validate_language(language: str) -> str:
    language = (language or "en").strip().lower()

    if not LANGUAGE_CODE_PATTERN.fullmatch(language):
        raise ValueError("Invalid Wikipedia language code.")

    return language


def clean_snippet(snippet: str) -> str:
    snippet = re.sub(r"<[^>]+>", "", snippet or "")
    return unescape(snippet).strip()


async def make_wikipedia_request(language: str, params: dict) -> dict:

    language = validate_language(language)

    api_url = f"https://{language}.wikipedia.org/w/api.php"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(
        timeout=25.0,
        headers=headers,
        follow_redirects=True
    ) as client:

        response = await client.get(api_url, params=params)

        response.raise_for_status()

        data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"].get("info", "Wikipedia API error."))

    return data


@tool
async def search_wikipedia(
    query: str,
    language: str = "en",
    limit: int = 5
) -> str:
    """Search Wikipedia articles and return JSON results."""

    if not query or not query.strip():
        return json_response({
            "success": False,
            "error": "Query cannot be empty.",
            "results": []
        })

    try:

        language = validate_language(language)

        limit = max(1, min(int(limit), 10))

        data = await make_wikipedia_request(
            language,
            {
                "action": "query",
                "list": "search",
                "srsearch": query.strip(),
                "srlimit": limit,
                "srprop": "snippet",
                "format": "json",
                "formatversion": 2
            }
        )

        search_items = data.get("query", {}).get("search", [])

        results = []

        for item in search_items:

            title = item.get("title", "")

            results.append({
                "title": title,
                "page_id": item.get("pageid"),
                "snippet": clean_snippet(item.get("snippet", "")),
                "url": (
                    f"https://{language}.wikipedia.org/wiki/"
                    f"{quote(title.replace(' ', '_'))}"
                )
            })

        return json_response({
            "success": True,
            "query": query,
            "language": language,
            "total_results": len(results),
            "results": results
        })

    except (httpx.HTTPError, ValueError, RuntimeError) as exc:

        return json_response({
            "success": False,
            "error": str(exc),
            "results": []
        })


@tool
async def get_wikipedia_article(
    title: str,
    language: str = "en",
    max_chars: int = 6000
) -> str:
    """Get Wikipedia article content in plain text JSON format."""

    if not title or not title.strip():
        return json_response({
            "success": False,
            "error": "Article title cannot be empty.",
            "article": None
        })

    try:

        language = validate_language(language)

        max_chars = max(500, min(int(max_chars), 10000))

        data = await make_wikipedia_request(
            language,
            {
                "action": "query",
                "prop": "extracts",
                "titles": title.strip(),
                "explaintext": 1,
                "exchars": max_chars,
                "redirects": 1,
                "format": "json",
                "formatversion": 2
            }
        )

        pages = data.get("query", {}).get("pages", [])

        if not pages or pages[0].get("missing"):

            return json_response({
                "success": False,
                "error": f"Article '{title}' was not found.",
                "article": None
            })

        page = pages[0]

        article_text = (page.get("extract") or "").strip()

        if not article_text:

            return json_response({
                "success": False,
                "error": "No readable article text found.",
                "article": None
            })

        page_title = page.get("title", title)

        article_url = (
            f"https://{language}.wikipedia.org/wiki/"
            f"{quote(page_title.replace(' ', '_'))}"
        )

        return json_response({
            "success": True,
            "language": language,
            "article": {
                "title": page_title,
                "page_id": page.get("pageid"),
                "text": article_text,
                "url": article_url,
                "truncated": len(article_text) >= max_chars
            }
        })

    except (httpx.HTTPError, ValueError, RuntimeError) as exc:

        return json_response({
            "success": False,
            "error": str(exc),
            "article": None
        })


def get_tools():

    return [
        search_wikipedia,
        get_wikipedia_article
    ]
