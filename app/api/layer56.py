from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import DetectionEvent, get_db
from app.models.schemas import Layer56Input, Layer56Response
from app.services.layer56_service import run_detection

router = APIRouter(prefix="/layer56", tags=["layer56"])


@router.post("/scan", response_model=Layer56Response)
def run_layer56_scan(payload: Layer56Input) -> Layer56Response:
    results = run_detection(
        content_id=payload.content_id,
        fingerprint_hash=payload.fingerprint_hash,
        watermark_id=payload.watermark_id,
        owner_id=payload.owner_id,
        blockchain_tx_hash=payload.blockchain_tx_hash,
        metadata=payload.metadata,
        ownership_verified=payload.ownership_verified,
    )
    return Layer56Response(
        success=True,
        content_id=payload.content_id,
        total_crawled=getattr(run_detection, "last_total_crawled", 0),
        detections_found=len(results),
        results=results,
    )


@router.get("/scan/{content_id}")
def get_last_scan_results(content_id: str, db: Session = Depends(get_db)) -> dict:
    rows = db.execute(
        select(DetectionEvent)
        .where(DetectionEvent.content_id == content_id)
        .order_by(DetectionEvent.id.desc())
    ).scalars()

    data = [
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

    return {"success": True, "data": data}
