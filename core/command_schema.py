from dataclasses import dataclass, field
from typing import Any


@dataclass
class StructuredCommand:
    intent: str = "automation"

    action: str | None = None

    target: str | None = None
    target_type: str | None = None

    application: str | None = None
    platform: str | None = None

    query: str | None = None
    text: str | None = None
    recipient: str | None = None

    arguments: dict[str, Any] = field(default_factory=dict)

    confidence: float = 1.0