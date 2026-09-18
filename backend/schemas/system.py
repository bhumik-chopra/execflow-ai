from datetime import datetime
from typing import Literal

from pydantic import BaseModel




class HealthResponse(BaseModel):
    backend: Literal["ok"] = "ok"
    mongodb: Literal["ok", "unavailable"]
    groq: Literal["configured", "unavailable"]
    groq_model: str


class ContextResponse(BaseModel):
    user: str = "Arjun Malhotra"
    role: str = "VP Sales"
    as_of: datetime
