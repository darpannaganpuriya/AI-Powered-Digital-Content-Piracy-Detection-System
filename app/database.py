import os
from datetime import datetime
from typing import Generator

from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = "sqlite:///./data/piracy_protection.db"


class Base(DeclarativeBase):
    pass


class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    similarity: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    leak_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    watermark_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    blockchain_tx_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detected_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class PiracyPrediction(Base):
    __tablename__ = "piracy_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    predicted_verdict: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    predicted_platforms: Mapped[str] = mapped_column(Text, nullable=False)
    detection_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class OwnerAlert(Base):
    __tablename__ = "owner_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    alert_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    owner_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    content_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    leak_source: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    action_taken: Mapped[str] = mapped_column(String(100), nullable=False)
    alert_time: Mapped[str] = mapped_column(String(64), nullable=False)


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dmca_notice: Mapped[str | None] = mapped_column(Text, nullable=True)
    redirect_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ExecutionLog(Base):
    __tablename__ = "execution_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    decision_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    execution_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables() -> None:
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
