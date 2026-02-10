from __future__ import annotations

from .http import HttpClient
from .payments import PaymentsClient
from .providers import ProvidersClient


class DelopayClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://sandbox-delopay.deloxity.com",
        timeout_ms: int = 30_000,
        max_retries: int = 2,
    ) -> None:
        http = HttpClient(
            api_key=api_key,
            base_url=base_url,
            timeout_ms=timeout_ms,
            max_retries=max_retries,
        )
        self.payments = PaymentsClient(http)
        self.providers = ProvidersClient(http)
