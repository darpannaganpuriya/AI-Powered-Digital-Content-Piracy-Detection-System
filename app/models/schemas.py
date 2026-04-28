from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class Layer12Input(BaseModel):
    content_id: str = Field(..., min_length=1)
    encrypted_media_path: str = Field(..., min_length=1)
    drm_license_info: str = Field(..., min_length=1)
    watermark_id: str = Field(..., min_length=1)
    fingerprint_hash: str = Field(..., min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Layer34Output(BaseModel):
    content_id: str
    fingerprint_hash: str
    watermark_id: str
    blockchain_tx_hash: str
    blockchain_network: str
    ownership_verified: bool
    feature_vector: list[float]
    ai_model_version: str
    registered_at: datetime

    @field_validator("registered_at", mode="before")
    @classmethod
    def ensure_utc_datetime(cls, value: Any) -> datetime:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone(timezone.utc)

        raise ValueError("registered_at must be a datetime or ISO datetime string")


class HealthResponse(BaseModel):
    status: str
    service: str


class DetectionInput(BaseModel):
    url: str
    platform: str
    similarity: float
    verdict: str
    confidence: float
    detected_at: Optional[str] = None
    content_id: Optional[str] = None
    watermark_id: Optional[str] = None
    owner_id: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    leak_source: Optional[str] = None
    action_required: Optional[str] = None


class PredictionResult(BaseModel):
    content_id: str
    risk_score: float
    predicted_verdict: str
    predicted_platforms: List[str]
    detection_count: int


class LeakResult(BaseModel):
    leak_type: str
    watermark_id: Optional[str]
    platform: str
    region: str
    leak_severity: str


class DecisionResult(BaseModel):
    action: str
    dmca_notice: Optional[str]
    redirect_url: Optional[str]


class AlertResult(BaseModel):
    alert_id: str
    owner_id: str
    content_id: str
    message: str
    action_taken: str
    alert_time: str


class ProcessResponse(BaseModel):
    success: bool
    detection_id: int
    content_id: Optional[str]
    verdict: str
    action_taken: str
    leak_type: str
    region: str
    risk_score: float
    predicted_verdict: str
    dmca_notice: Optional[str]
    redirect_url: Optional[str]
    alert_sent: bool
    processed_at: str


class Layer56Input(BaseModel):
    content_id: str
    fingerprint_hash: str
    watermark_id: str
    owner_id: str
    blockchain_tx_hash: str
    ownership_verified: bool = True
    metadata: dict = {}


class Layer56DetectionResult(BaseModel):
    url: str
    platform: str
    similarity: float
    verdict: str
    confidence: float
    risk: str
    action: str
    sample_hash: str
    reference_hash: str
    detected_at: str
    content_id: str
    watermark_id: str
    owner_id: str
    blockchain_tx_hash: str
    leak_source: str
    action_required: str
    ownership_verified: bool
    ai_analysis: Optional[dict] = None


class Layer56Response(BaseModel):
    success: bool
    content_id: str
    total_crawled: int
    detections_found: int
    results: List[Layer56DetectionResult]
