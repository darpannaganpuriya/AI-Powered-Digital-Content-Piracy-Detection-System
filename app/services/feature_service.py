import hashlib
import json
import math
from typing import Any


class FeatureService:
    def __init__(self, vector_size: int = 16) -> None:
        self._vector_size = vector_size

    def create_feature_vector(self, content_id: str, fingerprint_hash: str, metadata: dict[str, Any]) -> list[float]:
        canonical_metadata = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        seed = f"{content_id}|{fingerprint_hash}|{canonical_metadata}"

        values: list[float] = []
        for i in range(self._vector_size):
            block = hashlib.sha256(f"{seed}|{i}".encode("utf-8")).digest()
            raw = int.from_bytes(block[:4], byteorder="big", signed=False)
            values.append(raw / 2**32)

        norm = math.sqrt(sum(v * v for v in values))
        if norm == 0:
            return [0.0 for _ in values]

        return [round(v / norm, 6) for v in values]
