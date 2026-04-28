from datetime import datetime, timezone

import httpx

from app.config import settings
from app.models.schemas import Layer12Input, Layer34Output
from app.services.blockchain_service import BlockchainService
from app.services.feature_service import FeatureService
from app.services.repository import ContentRepository


class Layer34PipelineService:
    def __init__(self, repository: ContentRepository | None = None) -> None:
        self._blockchain_service = BlockchainService(
            network=settings.blockchain_network,
            tx_prefix=settings.blockchain_tx_prefix,
            secret_salt=settings.blockchain_salt,
        )
        self._feature_service = FeatureService(vector_size=16)
        self._repository = repository or ContentRepository()

    def process(self, payload: Layer12Input) -> Layer34Output:
        blockchain_tx_hash, ownership_verified = self._blockchain_service.register_ownership(
            content_id=payload.content_id,
            fingerprint_hash=payload.fingerprint_hash,
            watermark_id=payload.watermark_id,
        )

        feature_vector = self._feature_service.create_feature_vector(
            content_id=payload.content_id,
            fingerprint_hash=payload.fingerprint_hash,
            metadata=payload.metadata,
        )

        result = Layer34Output(
            content_id=payload.content_id,
            fingerprint_hash=payload.fingerprint_hash,
            watermark_id=payload.watermark_id,
            blockchain_tx_hash=blockchain_tx_hash,
            blockchain_network=self._blockchain_service.network,
            ownership_verified=ownership_verified,
            feature_vector=feature_vector,
            ai_model_version=settings.ai_model_version,
            registered_at=datetime.now(timezone.utc),
        )

        self._repository.upsert_result(layer_input=payload, output=result)

        # Trigger Layer 5-6 detection
        layer56_payload = {
            "content_id": result.content_id,
            "fingerprint_hash": result.fingerprint_hash,
            "watermark_id": result.watermark_id,
            "owner_id": payload.metadata.get("owner_id", ""),
            "blockchain_tx_hash": result.blockchain_tx_hash,
            "ownership_verified": result.ownership_verified,
            "metadata": payload.metadata,
        }
        try:
            httpx.post(
                "http://127.0.0.1:8000/api/v1/layer56/scan",
                json=layer56_payload,
                timeout=10.0,
            )
        except Exception:
            pass  # don't fail if Layer 5-6 is not running

        return result

    def get_registered_content(self, content_id: str) -> Layer34Output | None:
        return self._repository.get_result(content_id=content_id)
