from pydantic import BaseModel
from typing import Optional, Dict, Any


class AnalyticsQuery(BaseModel):
    query:   str
    context: Optional[Dict[str, Any]] = None


class AnalyticsResponse(BaseModel):
    answer:     str
    sources:    list = []
    disclaimer: str  = (
        "This is market data analysis, not investment advice. "
        "Consult a licensed financial advisor before making investment decisions."
    )
    error: Optional[str] = None