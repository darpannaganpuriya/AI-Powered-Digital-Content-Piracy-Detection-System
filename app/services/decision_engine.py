from datetime import datetime

from sqlalchemy.orm import Session

from app.database import Decision
from app.models.schemas import DecisionResult


def make_decision(
    db: Session,
    content_id: str,
    url: str,
    verdict: str,
    confidence: float,
    blockchain_tx_hash: str | None,
) -> DecisionResult:
    if confidence >= 0.9 and verdict == "PIRACY":
        action = "TAKEDOWN"
        dmca_notice = (
            f"DMCA Notice - Content ID: {content_id} | "
            f"Proof: {blockchain_tx_hash} | "
            f"Infringing URL: {url} | Issued: {datetime.utcnow()}"
        )
        redirect_url = None
    elif confidence >= 0.7 and verdict == "PIRACY":
        action = "REVENUE_REDIRECT"
        redirect_url = f"https://official-sports.com/watch/{content_id}"
        dmca_notice = None
    else:
        action = "MONITOR"
        dmca_notice = None
        redirect_url = None

    decision_row = Decision(
        content_id=content_id,
        url=url,
        action=action,
        dmca_notice=dmca_notice,
        redirect_url=redirect_url,
    )
    db.add(decision_row)
    db.commit()

    return DecisionResult(action=action, dmca_notice=dmca_notice, redirect_url=redirect_url)
