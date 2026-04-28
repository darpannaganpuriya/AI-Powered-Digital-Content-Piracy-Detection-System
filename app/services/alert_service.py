from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.database import OwnerAlert
from app.models.schemas import AlertResult


def send_alert(
    db: Session,
    owner_id: str,
    content_id: str,
    verdict: str,
    confidence: float,
    platform: str,
    leak_type: str,
    region: str,
    action: str,
) -> AlertResult:
    alert_id = str(uuid4())
    message = (
        f"ALERT: Your content {content_id} detected on {platform} "
        f"with {confidence * 100:.0f}% confidence. "
        f"Leak source: {leak_type}. Region: {region}. Action: {action}"
    )

    print(f"🚨 PIRACY ALERT [{verdict}] 🚨\\n{message}")

    alert_time = datetime.utcnow().isoformat()
    alert_row = OwnerAlert(
        alert_id=alert_id,
        owner_id=owner_id,
        content_id=content_id,
        message=message,
        leak_source=leak_type,
        region=region,
        action_taken=action,
        alert_time=alert_time,
    )
    db.add(alert_row)
    db.commit()

    return AlertResult(
        alert_id=alert_id,
        owner_id=owner_id,
        content_id=content_id,
        message=message,
        action_taken=action,
        alert_time=alert_time,
    )
