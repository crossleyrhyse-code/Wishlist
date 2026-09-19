from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ProductProfile:
    raw_title: str
    product_type: Optional[str] = None
    product_subtype: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    voltage: Optional[int] = None
    voltage_multiplier: Optional[int] = None
    size_mm: Optional[int] = None
    coverage_degrees: Optional[int] = None
    package: Optional[str] = None
    watts: Optional[int] = None
    amp_hours: Optional[float] = None
    battery_count: Optional[int] = None
    size_inches: Optional[float] = None
    is_accessory: bool = False
    is_bundle: bool = False
    attributes: dict = field(default_factory=dict)

@dataclass
class MatchResult:
    classification: str
    score: int
    reasons: list[str] = field(default_factory=list)
