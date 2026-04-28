import hashlib
import hmac


class BlockchainService:
    def __init__(self, network: str, tx_prefix: str, secret_salt: str) -> None:
        self._network = network
        self._tx_prefix = tx_prefix
        self._secret_salt = secret_salt.encode("utf-8")

    @property
    def network(self) -> str:
        return self._network

    def register_ownership(self, content_id: str, fingerprint_hash: str, watermark_id: str) -> tuple[str, bool]:
        message = f"{content_id}|{fingerprint_hash}|{watermark_id}".encode("utf-8")
        digest = hmac.new(self._secret_salt, message, hashlib.sha256).hexdigest()
        tx_hash = f"{self._tx_prefix}{digest}"
        return tx_hash, True
