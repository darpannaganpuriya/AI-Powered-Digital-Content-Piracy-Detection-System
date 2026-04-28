from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Decision, DetectionEvent, get_db
from app.models.schemas import DetectionInput, ProcessResponse
from app.services.alert_service import send_alert
from app.services.decision_engine import make_decision
from app.services.executor import execute_decision
from app.services.leak_identifier import identify_leak
from app.services.predictor import run_prediction

router = APIRouter(prefix="/decision", tags=["decision"])


@router.post("/process")
def process_detection(payload: DetectionInput, db: Session = Depends(get_db)) -> dict:
    content_id = payload.content_id or "unknown_content"
    owner_id = payload.owner_id or "unknown_owner"

    detection = DetectionEvent(
        content_id=content_id,
        url=payload.url,
        platform=payload.platform,
        similarity=payload.similarity,
        verdict=payload.verdict,
        confidence=payload.confidence,
        leak_source=payload.leak_source,
        watermark_id=payload.watermark_id,
        owner_id=owner_id,
        blockchain_tx_hash=payload.blockchain_tx_hash,
        detected_at=payload.detected_at,
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)

    prediction = run_prediction(
        db=db,
        content_id=content_id,
        platform=payload.platform,
        similarity=payload.similarity,
        confidence=payload.confidence,
    )
    leak = identify_leak(watermark_id=payload.watermark_id, platform=payload.platform)
    decision = make_decision(
        db=db,
        content_id=content_id,
        url=payload.url,
        verdict=payload.verdict,
        confidence=payload.confidence,
        blockchain_tx_hash=payload.blockchain_tx_hash,
    )

    alert = send_alert(
        db=db,
        owner_id=owner_id,
        content_id=content_id,
        verdict=payload.verdict,
        confidence=payload.confidence,
        platform=payload.platform,
        leak_type=leak.leak_type,
        region=leak.region,
        action=decision.action,
    )

    decision_id = db.scalar(
        select(Decision.id)
        .where(Decision.content_id == content_id, Decision.url == payload.url)
        .order_by(Decision.id.desc())
    )
    execute_decision(
        db=db,
        decision_id=int(decision_id or 0),
        action=decision.action,
        dmca_notice=decision.dmca_notice,
        redirect_url=decision.redirect_url,
        content_id=content_id,
        url=payload.url,
    )

    response = ProcessResponse(
        success=True,
        detection_id=detection.id,
        content_id=content_id,
        verdict=payload.verdict,
        action_taken=decision.action,
        leak_type=leak.leak_type,
        region=leak.region,
        risk_score=prediction.risk_score,
        predicted_verdict=prediction.predicted_verdict,
        dmca_notice=decision.dmca_notice,
        redirect_url=decision.redirect_url,
        alert_sent=bool(alert.alert_id),
        processed_at=datetime.utcnow().isoformat(),
    )
    return {"success": True, "data": response.model_dump()}
