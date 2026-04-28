import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.models.schemas import Layer12Input, Layer34Output


class ContentRepository:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or settings.database_path
        self._init_database()

    def _init_database(self) -> None:
        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_registry (
                    content_id TEXT PRIMARY KEY,
                    fingerprint_hash TEXT NOT NULL,
                    watermark_id TEXT NOT NULL,
                    blockchain_tx_hash TEXT NOT NULL,
                    blockchain_network TEXT NOT NULL,
                    ownership_verified INTEGER NOT NULL,
                    feature_vector_json TEXT NOT NULL,
                    ai_model_version TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    encrypted_media_path TEXT NOT NULL,
                    drm_license_info TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def upsert_result(self, layer_input: Layer12Input, output: Layer34Output) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                """
                INSERT INTO content_registry (
                    content_id,
                    fingerprint_hash,
                    watermark_id,
                    blockchain_tx_hash,
                    blockchain_network,
                    ownership_verified,
                    feature_vector_json,
                    ai_model_version,
                    registered_at,
                    encrypted_media_path,
                    drm_license_info,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(content_id) DO UPDATE SET
                    fingerprint_hash=excluded.fingerprint_hash,
                    watermark_id=excluded.watermark_id,
                    blockchain_tx_hash=excluded.blockchain_tx_hash,
                    blockchain_network=excluded.blockchain_network,
                    ownership_verified=excluded.ownership_verified,
                    feature_vector_json=excluded.feature_vector_json,
                    ai_model_version=excluded.ai_model_version,
                    registered_at=excluded.registered_at,
                    encrypted_media_path=excluded.encrypted_media_path,
                    drm_license_info=excluded.drm_license_info,
                    metadata_json=excluded.metadata_json
                """,
                (
                    output.content_id,
                    output.fingerprint_hash,
                    output.watermark_id,
                    output.blockchain_tx_hash,
                    output.blockchain_network,
                    int(output.ownership_verified),
                    json.dumps(output.feature_vector),
                    output.ai_model_version,
                    output.registered_at.isoformat(),
                    layer_input.encrypted_media_path,
                    layer_input.drm_license_info,
                    json.dumps(layer_input.metadata, separators=(",", ":"), sort_keys=True),
                ),
            )
            conn.commit()

    def get_result(self, content_id: str) -> Layer34Output | None:
        with sqlite3.connect(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT
                    content_id,
                    fingerprint_hash,
                    watermark_id,
                    blockchain_tx_hash,
                    blockchain_network,
                    ownership_verified,
                    feature_vector_json,
                    ai_model_version,
                    registered_at
                FROM content_registry
                WHERE content_id = ?
                """,
                (content_id,),
            ).fetchone()

        if row is None:
            return None

        return Layer34Output(
            content_id=row[0],
            fingerprint_hash=row[1],
            watermark_id=row[2],
            blockchain_tx_hash=row[3],
            blockchain_network=row[4],
            ownership_verified=bool(row[5]),
            feature_vector=json.loads(row[6]),
            ai_model_version=row[7],
            registered_at=datetime.fromisoformat(row[8]),
        )
