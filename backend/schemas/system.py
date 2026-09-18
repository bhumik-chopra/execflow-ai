from datetime import datetime
from typing import Literal

from pydantic import BaseModel


DEFAULT_AS_OF = datetime(2026, 9, 25, 9, 0, 0)


class HealthResponse(BaseModel):
    backend: Literal["ok"] = "ok"
    mongodb: Literal["ok", "unavailable"]
    groq: Literal["configured", "unavailable"]
    groq_model: str


class ContextResponse(BaseModel):
    user: str = "Arjun Malhotra"
    role: str = "VP Sales"
    as_of: datetime
