import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import DetectionEvent, PiracyPrediction
from app.models.schemas import PredictionResult


def run_prediction(
    db: Session,
    content_id: str,
    platform: str,
    similarity: float,
    confidence: float,
) -> PredictionResult:
    detection_count = db.scalar(
        select(func.count(DetectionEvent.id)).where(DetectionEvent.content_id == content_id)
    )
    detection_count = int(detection_count or 0)

    risk_score = min(1.0, (detection_count * similarity * confidence) / 3)

    if risk_score > 0.8:
        predicted_verdict = "HIGH_RISK"
    elif risk_score > 0.5:
        predicted_verdict = "MEDIUM_RISK"
    else:
        predicted_verdict = "LOW_RISK"

    platform_map = {
        "youtube": ["telegram", "hotstar"],
        "telegram": ["piracy_sites", "youtube"],
    }
    predicted_platforms = platform_map.get(platform.lower(), ["telegram", "torrent_sites"])

    prediction_row = PiracyPrediction(
        content_id=content_id,
        risk_score=risk_score,
        predicted_verdict=predicted_verdict,
        predicted_platforms=json.dumps(predicted_platforms),
        detection_count=detection_count,
    )
    db.add(prediction_row)
    db.commit()

    return PredictionResult(
        content_id=content_id,
        risk_score=risk_score,
        predicted_verdict=predicted_verdict,
        predicted_platforms=predicted_platforms,
        detection_count=detection_count,
    )
