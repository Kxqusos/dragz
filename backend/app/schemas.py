from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator

PASSWORD_REQUIREMENTS_ERROR = "Пароль должен содержать минимум 8 символов, маленькие и большие буквы, а также цифры."


def validate_password_complexity(password: str) -> str:
    if len(password) < 8:
        raise ValueError(PASSWORD_REQUIREMENTS_ERROR)
    if not any(character.islower() for character in password):
        raise ValueError(PASSWORD_REQUIREMENTS_ERROR)
    if not any(character.isupper() for character in password):
        raise ValueError(PASSWORD_REQUIREMENTS_ERROR)
    if not any(character.isdigit() for character in password):
        raise ValueError(PASSWORD_REQUIREMENTS_ERROR)
    return password


class Suggestion(BaseModel):
    id: str
    title: str
    kind: str
    confidence: float
    rationale: str


class PharmacyOffer(BaseModel):
    pharmacy_id: str
    pharmacy_name: str
    address: str
    lat: float
    lon: float
    price: float
    in_stock: bool = True
    quantity_label: str
    matched_drug: str


class SearchResponse(BaseModel):
    mode: str
    suggestions: list[Suggestion] = Field(default_factory=list)
    offers: list[PharmacyOffer] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OriginPoint(BaseModel):
    lat: float
    lon: float


class RoutePharmacy(BaseModel):
    pharmacy_id: str = Field(validation_alias=AliasChoices("pharmacy_id", "pharmacyId"))
    pharmacy_name: str = Field(validation_alias=AliasChoices("pharmacy_name", "pharmacyName"))
    address: str | None = None
    lat: float
    lon: float


class RouteRequest(BaseModel):
    origin: OriginPoint
    pharmacies: list[RoutePharmacy]


class RouteStop(BaseModel):
    pharmacy_id: str
    label: str
    lat: float
    lon: float
    order: int


class RouteResponse(BaseModel):
    total_duration_minutes: int
    total_distance_km: float
    ordered_stops: list[RouteStop]
    route_geometry: list[list[float]] = Field(default_factory=list)


class AIChatMessage(BaseModel):
    role: str
    content: str


class OTCDrugRecommendation(BaseModel):
    title: str
    rationale: str


class AIChatHandoff(BaseModel):
    label: str
    query: str


class AIChatRequest(BaseModel):
    messages: list[AIChatMessage] = Field(default_factory=list)


class AIChatResponse(BaseModel):
    scope_status: str
    message: str
    warnings: list[str] = Field(default_factory=list)
    recommended_otc_drugs: list[OTCDrugRecommendation] = Field(default_factory=list)
    handoff_cta: AIChatHandoff | None = None


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: EmailStr
    password: str = Field(max_length=128)
    accepted_terms: Literal[True] = Field(validation_alias=AliasChoices("accepted_terms", "acceptedTerms"))

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_complexity(value)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=4, max_length=16)
    password: str = Field(max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_password_complexity(value)


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_blocked: bool
    is_email_verified: bool
    created_at: str


class AuthMessageResponse(BaseModel):
    message: str


class CartItemPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pharmacy_id: str = Field(validation_alias=AliasChoices("pharmacy_id", "pharmacyId"))
    pharmacy_name: str = Field(validation_alias=AliasChoices("pharmacy_name", "pharmacyName"))
    address: str
    lat: float
    lon: float
    price: float
    in_stock: bool = Field(default=True, validation_alias=AliasChoices("in_stock", "inStock"))
    quantity_label: str = Field(validation_alias=AliasChoices("quantity_label", "quantityLabel"))
    matched_drug: str = Field(validation_alias=AliasChoices("matched_drug", "matchedDrug"))


class CartResponse(BaseModel):
    items: list[CartItemPayload] = Field(default_factory=list)


class SearchHistoryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str
    created_at: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class SearchHistoryResponse(BaseModel):
    items: list[SearchHistoryItem] = Field(default_factory=list)


class AIConversationMeta(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    scope_status: str = Field(validation_alias=AliasChoices("scope_status", "scopeStatus"))
    warnings: list[str] = Field(default_factory=list)
    recommended_otc_drugs: list[OTCDrugRecommendation] = Field(
        default_factory=list,
        validation_alias=AliasChoices("recommended_otc_drugs", "recommendedOTCDrugs"),
    )
    handoff_cta: AIChatHandoff | None = Field(
        default=None,
        validation_alias=AliasChoices("handoff_cta", "handoffCTA"),
    )


class AIConversationItemPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: str
    content: str
    meta: AIConversationMeta | None = None


class AIConversationPayload(BaseModel):
    id: int
    created_at: str
    messages: list[AIConversationItemPayload] = Field(default_factory=list)


class AIHistoryResponse(BaseModel):
    items: list[AIConversationPayload] = Field(default_factory=list)


class MergeGuestStateRequest(BaseModel):
    cart_items: list[CartItemPayload] = Field(
        default_factory=list,
        validation_alias=AliasChoices("cart_items", "cartItems"),
    )
    search_history: list[SearchHistoryItem] = Field(
        default_factory=list,
        validation_alias=AliasChoices("search_history", "searchHistory"),
    )
    ai_conversation: list[AIConversationItemPayload] = Field(
        default_factory=list,
        validation_alias=AliasChoices("ai_conversation", "aiConversation"),
    )


class DebugEventRequest(BaseModel):
    event: str
    route: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class DebugEventResponse(BaseModel):
    id: int
    event: str
    route: str | None = None
    request_id: str | None = None
    user_agent: str | None = None
    ip_hash: str | None = None
    anonymous_id: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: str


class DebugEventsResponse(BaseModel):
    items: list[DebugEventResponse] = Field(default_factory=list)


class AdminUsersResponse(BaseModel):
    items: list[UserResponse] = Field(default_factory=list)


class AdminUserPatchRequest(BaseModel):
    role: str | None = None
    is_blocked: bool | None = Field(default=None, validation_alias=AliasChoices("is_blocked", "isBlocked"))


class SiteSettingItem(BaseModel):
    key: str
    value: object | None = None


class SiteSettingsResponse(BaseModel):
    items: list[SiteSettingItem] = Field(default_factory=list)


class SiteSettingsUpdateRequest(BaseModel):
    items: list[SiteSettingItem] = Field(default_factory=list)
