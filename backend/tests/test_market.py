"""
Tests: Market data endpoints
/api/market/stocks, /api/market/stocks/{symbol}, /api/market/anomalies
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app

client = TestClient(app)


class TestStockList:
    def test_nse_stocks_returns_200(self):
        mock_data = [
            {
                "symbol": "SCOM", "name": "Safaricom PLC", "exchange": "NSE",
                "close": 18.50, "change_pct": 1.2, "volume": 1_000_000,
                "date": "2026-06-20", "data_quality_warning": None,
            }
        ]
        with patch("app.services.market.get_stocks", new_callable=AsyncMock, return_value=mock_data):
            res = client.get("/api/market/stocks?exchange=NSE")
        assert res.status_code == 200
        body = res.json()
        assert "data" in body
        assert body["exchange"] == "NSE"
        assert "disclaimer" in body

    def test_invalid_exchange_returns_400(self):
        res = client.get("/api/market/stocks?exchange=INVALID")
        assert res.status_code == 400

    def test_disclaimer_always_present(self):
        with patch("app.services.market.get_stocks", new_callable=AsyncMock, return_value=[]):
            res = client.get("/api/market/stocks")
        assert "disclaimer" in res.json()


class TestStockDetail:
    def test_known_symbol(self):
        mock_detail = {
            "symbol": "EQTY", "exchange": "NSE",
            "history": [{"date": "2026-06-20", "close": 55.00, "volume": 200_000}],
            "days": 90,
        }
        with patch("app.services.market.get_stock_detail", new_callable=AsyncMock, return_value=mock_detail):
            res = client.get("/api/market/stocks/EQTY")
        assert res.status_code == 200

    def test_unknown_symbol_returns_404(self):
        with patch("app.services.market.get_stock_detail", new_callable=AsyncMock, return_value=None):
            res = client.get("/api/market/stocks/XXXX")
        assert res.status_code == 404


class TestAnomalies:
    def test_anomalies_structure(self):
        mock_flags = [
            {
                "symbol": "KCB", "exchange": "NSE", "date": "2026-06-18",
                "anomaly_type": "volume_spike", "anomaly_score": 0.87,
                "description": "Volume 3× 30-day average",
                "disclaimer": "Statistical anomaly only.",
            }
        ]
        with patch("app.services.market.get_anomalies", new_callable=AsyncMock, return_value=mock_flags):
            res = client.get("/api/market/anomalies?exchange=NSE&days=7")
        assert res.status_code == 200
        body = res.json()
        assert "flags" in body
        assert "disclaimer" in body
        assert body["count"] == 1