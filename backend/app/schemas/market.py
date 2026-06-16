from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class StockQuote(BaseModel):
    symbol:               str
    name:                 Optional[str]
    exchange:             str
    close:                float
    volume:               Optional[int]
    change_pct:           Optional[float]
    date:                 Optional[date]
    sector:               Optional[str]
    data_quality_warning: Optional[str]
    source:               str = "afx.kwayisi.org"


class StockListResponse(BaseModel):
    exchange:   str
    count:      int
    data:       List[StockQuote]
    disclaimer: str


class OHLCVPoint(BaseModel):
    date:   date
    open:   Optional[float]
    high:   Optional[float]
    low:    Optional[float]
    close:  float
    volume: Optional[int]


class StockDetailResponse(BaseModel):
    symbol:    str
    exchange:  str
    history:   List[OHLCVPoint]
    days:      int


class ForecastResponse(BaseModel):
    symbol:              str
    exchange:            str
    forecast_date:       str
    horizon_days:        int
    directional_signal:  str          # bullish | bearish | neutral
    probability_up:      float
    forecast_return_pct: float
    ci_low:              float
    ci_high:             float
    model_version:       str
    model_accuracy:      Optional[float]
    trained_on:          Optional[str]
    disclaimer:          str
    error:               Optional[str] = None


class AnomalyFlag(BaseModel):
    symbol:        str
    exchange:      str
    date:          Optional[str]
    anomaly_type:  str
    anomaly_score: float
    description:   str
    disclaimer:    str


class AnomalyResponse(BaseModel):
    exchange:   str
    days:       int
    count:      int
    flags:      List[AnomalyFlag]
    disclaimer: str