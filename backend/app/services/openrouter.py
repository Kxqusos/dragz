import json

from openai import AsyncOpenAI
from pydantic import TypeAdapter

from app.core.config import Settings
from app.schemas import Suggestion


_SUGGESTIONS_ADAPTER = TypeAdapter(list[Suggestion])


def build_suggestion_prompt(query: str) -> str:
    return (
        "Return JSON only with the shape "
        '{"suggestions":[{"id":"...","title":"...","kind":"drug","confidence":0.0,"rationale":"..."}]}. '
        "Do not invent pharmacies, prices, or inventory. "
        f"User query: {query}"
    )


def create_openrouter_client(settings: Settings) -> AsyncOpenAI:
    headers = {}

    if settings.openrouter_http_referer:
        headers["HTTP-Referer"] = settings.openrouter_http_referer
    if settings.openrouter_title:
        headers["X-OpenRouter-Title"] = settings.openrouter_title

    return AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers=headers or None,
    )


def normalize_openrouter_suggestions(content: str) -> list[Suggestion]:
    payload = json.loads(content)
    suggestions = payload.get("suggestions", [])
    return _SUGGESTIONS_ADAPTER.validate_python(suggestions)


async def suggest_drugs(query: str, settings: Settings) -> list[Suggestion]:
    if not settings.openrouter_api_key or not settings.openrouter_model:
        return []

    client = create_openrouter_client(settings)
    completion = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[{"role": "user", "content": build_suggestion_prompt(query)}],
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    if not content:
        return []

    return normalize_openrouter_suggestions(content)
