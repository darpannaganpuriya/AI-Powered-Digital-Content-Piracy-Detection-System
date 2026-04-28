from app.models.schemas import Layer12Input
from app.services.pipeline_service import Layer34PipelineService


def test_layer34_output_contract() -> None:
    service = Layer34PipelineService()
    payload = Layer12Input(
        content_id="123",
        encrypted_media_path="s3://bucket/encrypted/123.mpd",
        drm_license_info="widevine:license_server_1",
        watermark_id="user_456",
        fingerprint_hash="abcxyz123",
        metadata={"sport": "football", "owner_id": "org_123"},
    )

    result = service.process(payload)

    assert result.content_id == "123"
    assert result.fingerprint_hash == "abcxyz123"
    assert result.watermark_id == "user_456"
    assert result.blockchain_tx_hash.startswith("0x")
    assert result.blockchain_network == "polygon_mumbai"
    assert result.ownership_verified is True
    assert len(result.feature_vector) == 16
    assert result.ai_model_version == "v1.0"
