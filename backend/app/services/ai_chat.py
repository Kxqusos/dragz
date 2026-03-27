import json
import re

from pydantic import TypeAdapter

from app.core.config import Settings
from app.schemas import AIChatMessage, AIChatResponse, OTCDrugRecommendation, AIChatHandoff
from app.services.openrouter import create_openrouter_client


REFUSAL_MESSAGE = "Я не могу помочь с этим вопросом. Я могу отвечать только по симптомам и безрецептурным препаратам."
UNAVAILABLE_MESSAGE = "Сервис консультации временно недоступен. Попробуйте позже."
_AI_CHAT_RESPONSE_ADAPTER = TypeAdapter(AIChatResponse)
_NON_DRUG_PATTERNS = (
    "аптеки",
    "аптека",
    "рядом",
    "поиск",
    "маршрут",
    "консульт",
)


def build_otc_chat_prompt(latest_user_message: str) -> str:
    return (
        "Return JSON only with the shape "
        '{"scope_status":"refused|otc_advice|doctor_referral","message":"...","warnings":["..."],'
        '"recommended_otc_drugs":[{"title":"...","rationale":"..."}],"handoff_cta":{"label":"...","query":"..."}}. '
        "You are an OTC-only assistant for Russian-speaking users. "
        "Help only with symptoms and over-the-counter medicines. "
        "Do not discuss unrelated topics. Do not diagnose. Do not recommend prescription medicines. "
        "If the user asks something outside symptoms or over-the-counter medicines, return scope_status='refused' "
        f"and message='{REFUSAL_MESSAGE}'. "
        "If the symptoms look risky or need a doctor, return scope_status='doctor_referral' with a brief warning. "
        "For valid OTC help, return scope_status='otc_advice' and optionally suggest over-the-counter medicines "
        "with a handoff_cta that leads to pharmacy search. "
        "Recommendation titles must contain only the medicine name itself, with no examples in brackets, "
        "no pharmacy phrases, and no navigation wording. "
        f"Latest user message: {latest_user_message}. "
        "Не обсуждай посторонние темы."
    )


def normalize_otc_chat_response(payload: str | dict) -> AIChatResponse:
    raw_payload = json.loads(payload) if isinstance(payload, str) else payload
    response = _AI_CHAT_RESPONSE_ADAPTER.validate_python(raw_payload)
    cleaned_recommendations = _sanitize_recommendations(response.recommended_otc_drugs)
    response = response.model_copy(update={"recommended_otc_drugs": cleaned_recommendations})

    if response.scope_status == "otc_advice" and response.handoff_cta is None and response.recommended_otc_drugs:
        first_recommendation = response.recommended_otc_drugs[0]
        response = response.model_copy(
            update={
                "handoff_cta": AIChatHandoff(
                    label="Найти в аптеках",
                    query=first_recommendation.title,
                )
            }
        )

    if response.scope_status == "refused" and not response.message.strip():
        response = response.model_copy(update={"message": REFUSAL_MESSAGE})

    return response


def _sanitize_recommendations(recommendations: list[OTCDrugRecommendation]) -> list[OTCDrugRecommendation]:
    cleaned: list[OTCDrugRecommendation] = []

    for recommendation in recommendations:
        normalized_title = _sanitize_recommendation_title(recommendation.title)
        if not normalized_title or _looks_like_non_drug_title(normalized_title):
            continue

        cleaned.append(recommendation.model_copy(update={"title": normalized_title}))

    return cleaned


def _sanitize_recommendation_title(title: str) -> str:
    without_parentheses = re.sub(r"\s*\([^)]*\)", "", title).strip()
    normalized = re.sub(r"\s+", " ", without_parentheses).strip(" .,-")
    return normalized


def _looks_like_non_drug_title(title: str) -> bool:
    lowered = title.lower()
    return any(pattern in lowered for pattern in _NON_DRUG_PATTERNS)


async def run_otc_chat(messages: list[AIChatMessage], settings: Settings) -> AIChatResponse:
    if not settings.openrouter_api_key or not settings.openrouter_model:
        return AIChatResponse(
            scope_status="unavailable",
            message=UNAVAILABLE_MESSAGE,
            warnings=["ai-chat-unavailable"],
        )

    latest_user_message = next((message.content for message in reversed(messages) if message.role == "user"), "")
    client = create_openrouter_client(settings)
    completion = await client.chat.completions.create(
        model=settings.openrouter_model,
        messages=[
            {"role": "system", "content": build_otc_chat_prompt(latest_user_message)},
            *[
                {"role": message.role, "content": message.content}
                for message in messages
                if message.role in {"user", "assistant"}
            ],
        ],
        response_format={"type": "json_object"},
    )

    content = completion.choices[0].message.content
    if not content:
        return AIChatResponse(
            scope_status="unavailable",
            message=UNAVAILABLE_MESSAGE,
            warnings=["ai-chat-empty-response"],
        )

    return normalize_otc_chat_response(content)
