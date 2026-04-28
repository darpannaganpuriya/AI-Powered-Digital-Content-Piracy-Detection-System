from sqlalchemy.orm import Session

from app.database import ExecutionLog


def execute_decision(
    db: Session,
    decision_id: int,
    action: str,
    dmca_notice: str | None,
    redirect_url: str | None,
    content_id: str,
    url: str,
) -> dict:
    if action == "TAKEDOWN":
        message = f"DMCA EXECUTION for {content_id} at {url}: {dmca_notice}"
        print(f"[TAKEDOWN] {message}")
        status = "EXECUTED"
    elif action == "REVENUE_REDIRECT":
        message = f"REDIRECT EXECUTION: {url} -> {redirect_url}"
        print(f"[REVENUE_REDIRECT] {message}")
        status = "EXECUTED"
    else:
        message = f"MONITORING content {content_id} at {url}"
        status = "MONITORING"

    log_row = ExecutionLog(
        decision_id=decision_id,
        execution_type=action,
        status=status,
        message=message,
    )
    db.add(log_row)
    db.commit()

    return {"executed": True, "action": action, "status": status}
