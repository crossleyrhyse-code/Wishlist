from dataclasses import dataclass
from typing import Optional
@dataclass
class RetailerProduct:
    retailer: str
    title: str
    url: str
    price: Optional[float] = None
    price_text: Optional[str] = None
