from pydantic import AliasChoices, BaseModel, Field


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
