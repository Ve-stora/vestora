"""
Vestora output framing — enforces data-vendor legal posture.
Every analytics output must pass through these before hitting the API response.
"""

from typing import Any, Dict

DISCLAIMER = (
    "This is market data analysis, not investment advice. "
    "Consult a licensed financial advisor before making investment decisions."
)

ANOMALY_DISCLAIMER = (
    "Anomaly detection identifies statistical outliers in market data. "
    "It does not constitute investment advice or imply knowledge of any specific corporate event."
)

FORECAST_DISCLAIMER = (
    "Model forecast based on historical price and volume data. "
    "Not investment advice. Past model accuracy does not guarantee future results."
)


def frame_as_observation(raw_text: str) -> str:
    """
    Reframe LLM output as data observation, not advice.
    Strips advisory language patterns and replaces with data-vendor framing.
    """
    replacements = {
        "you should buy":      "the data suggests upward momentum for",
        "you should sell":     "the data indicates downward pressure on",
        "I recommend":         "the model indicates",
        "consider buying":     "historical patterns show bullish signals for",
        "consider selling":    "historical patterns show bearish signals for",
        "is a good investment":"shows positive momentum indicators",
        "is a bad investment": "shows negative momentum indicators",
        "will go up":          "has a bullish model signal",
        "will go down":        "has a bearish model signal",
        "will increase":       "has an upward model forecast",
        "will decrease":       "has a downward model forecast",
    }
    text = raw_text
    for advisory, safe in replacements.items():
        text = text.replace(advisory, safe)
    return text


def wrap_forecast(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure forecast response always includes disclaimer and compliant signal language."""
    data["disclaimer"] = FORECAST_DISCLAIMER
    return data


def wrap_anomaly(data: Dict[str, Any]) -> Dict[str, Any]:
    data["disclaimer"] = ANOMALY_DISCLAIMER
    return data


def wrap_analytics(text: str) -> Dict[str, Any]:
    return {
        "answer":     frame_as_observation(text),
        "disclaimer": DISCLAIMER,
        "sources":    ["NSE market data via afx.kwayisi.org", "Vestora ML models"],
    }