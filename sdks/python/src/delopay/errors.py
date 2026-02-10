from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ApiError(Exception):
    status: int
    message: str
    code: str | None = None
    request_id: str | None = None
    raw: Any = None

    def __str__(self) -> str:
        return f"ApiError(status={self.status}, message={self.message})"
