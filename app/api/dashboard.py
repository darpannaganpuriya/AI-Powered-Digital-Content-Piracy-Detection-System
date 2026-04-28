import json

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import Decision, DetectionEvent, OwnerAlert, PiracyPrediction, get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)) -> dict:
    total_detections = int(db.scalar(select(func.count(DetectionEvent.id))) or 0)
    piracy_count = int(
        db.scalar(
            select(func.count(DetectionEvent.id)).where(DetectionEvent.verdict == "PIRACY")
        )
        or 0
    )
    suspicious_count = int(
        db.scalar(
            select(func.count(DetectionEvent.id)).where(
                DetectionEvent.verdict == "SUSPICIOUS"
            )
        )
        or 0
    )
    takedowns_executed = int(
        db.scalar(select(func.count(Decision.id)).where(Decision.action == "TAKEDOWN")) or 0
    )
    revenue_redirects = int(
        db.scalar(
            select(func.count(Decision.id)).where(Decision.action == "REVENUE_REDIRECT")
        )
        or 0
    )

    high_risk_rows = db.execute(
        select(PiracyPrediction.content_id, PiracyPrediction.risk_score)
        .where(PiracyPrediction.predicted_verdict == "HIGH_RISK")
        .order_by(desc(PiracyPrediction.risk_score))
        .limit(10)
    ).all()
    high_risk_content = [
        {"content_id": row.content_id, "risk_score": row.risk_score} for row in high_risk_rows
    ]

    top_platform_rows = db.execute(
        select(DetectionEvent.platform, func.count(DetectionEvent.id).label("count"))
        .group_by(DetectionEvent.platform)
        .order_by(desc("count"))
        .limit(5)
    ).all()
    top_platforms = [
        {"platform": row.platform, "count": row.count} for row in top_platform_rows
    ]

    summary = {
        "total_detections": total_detections,
        "piracy_count": piracy_count,
        "suspicious_count": suspicious_count,
        "takedowns_executed": takedowns_executed,
        "revenue_redirects": revenue_redirects,
        "high_risk_content": high_risk_content,
        "top_platforms": top_platforms,
    }
    return {"success": True, "data": summary}


@router.get("/detections")
def get_detections(
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    page = max(1, page)
    limit = max(1, min(limit, 100))
    offset = (page - 1) * limit

    total = int(db.scalar(select(func.count(DetectionEvent.id))) or 0)
    rows = db.execute(
        select(DetectionEvent).order_by(DetectionEvent.id.desc()).offset(offset).limit(limit)
    ).scalars()
    detections = [
        {
            "id": row.id,
            "content_id": row.content_id,
            "url": row.url,
            "platform": row.platform,
            "similarity": row.similarity,
            "verdict": row.verdict,
            "confidence": row.confidence,
            "leak_source": row.leak_source,
            "watermark_id": row.watermark_id,
            "owner_id": row.owner_id,
            "blockchain_tx_hash": row.blockchain_tx_hash,
            "detected_at": row.detected_at,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]

    data = {"page": page, "limit": limit, "total": total, "items": detections}
    return {"success": True, "data": data}


@router.get("/alerts/{owner_id}")
def get_alerts(owner_id: str, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(OwnerAlert)
        .where(OwnerAlert.owner_id == owner_id)
        .order_by(OwnerAlert.id.desc())
    ).scalars()

    alerts = [
        {
            "id": row.id,
            "alert_id": row.alert_id,
            "owner_id": row.owner_id,
            "content_id": row.content_id,
            "message": row.message,
            "leak_source": row.leak_source,
            "region": row.region,
            "action_taken": row.action_taken,
            "alert_time": row.alert_time,
        }
        for row in rows
    ]

    return {"success": True, "data": alerts}


@router.get("/predictions")
def get_predictions(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(PiracyPrediction).order_by(PiracyPrediction.id.desc())
    ).scalars()

    predictions = [
        {
            "id": row.id,
            "content_id": row.content_id,
            "risk_score": row.risk_score,
            "predicted_verdict": row.predicted_verdict,
            "predicted_platforms": json.loads(row.predicted_platforms),
            "detection_count": row.detection_count,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]

    return {"success": True, "data": predictions}


@router.get("/decisions")
def get_decisions(db: Session = Depends(get_db)) -> dict:
    rows = db.execute(select(Decision).order_by(Decision.id.desc())).scalars()

    decisions = [
        {
            "id": row.id,
            "content_id": row.content_id,
            "url": row.url,
            "action": row.action,
            "dmca_notice": row.dmca_notice,
            "redirect_url": row.redirect_url,
            "decided_at": row.decided_at.isoformat(),
        }
        for row in rows
    ]

    return {"success": True, "data": decisions}
