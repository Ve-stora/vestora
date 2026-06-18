"""
NSE / USE Data Scraper
=======================
Fetches end-of-day equity data from afx.kwayisi.org — the most reliable
free source for NSE and USE market data.

Design principles:
  - Async HTTP with retry + exponential back-off
  - Rate limiting (1 req/sec — respectful of free data source)
  - Robust parsing: handles missing columns, zero-volume days, stale prices
  - All data quality issues surfaced as warnings, never silently dropped
  - Stateless: safe to call concurrently from multiple workers
"""

import asyncio
import logging
from datetime import date, datetime
from typing import Dict, List, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

NSE_URL = "https://afx.kwayisi.org/nse/"
USE_URL = "https://afx.kwayisi.org/use/"

REQUEST_TIMEOUT   = 20.0   # seconds
MAX_RETRIES       = 3
RETRY_BASE_DELAY  = 2.0    # seconds; doubles each retry
RATE_LIMIT_DELAY  = 1.0    # seconds between requests

HEADERS = {
    "User-Agent": (
        "Vestora/0.1 Market Intelligence Platform "
        "(East African Capital Markets Analytics; "
        "contact: veritasndiema@gmail.com)"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Scraper ──────────────────────────────────────────────────────────────────

class NSEScraper:
    """
    Async scraper for afx.kwayisi.org NSE and USE equity tables.

    Usage:
        raw  = await scraper.fetch_nse_stocks()
        data = scraper.validate(raw)
    """

    def __init__(self) -> None:
        self._last_request_at: float = 0.0
        self._lock = asyncio.Lock()

    # ── Public fetch methods ─────────────────────────────────────────────────

    async def fetch_nse_stocks(self) -> List[Dict]:
        """Fetch current NSE equity prices. Returns list of raw stock dicts."""
        logger.info("Fetching NSE stocks from afx.kwayisi.org/nse/")
        html = await self._fetch_with_retry(NSE_URL)
        return self._parse_stock_table(html, exchange="NSE")

    async def fetch_use_stocks(self) -> List[Dict]:
        """Fetch current USE equity prices."""
        logger.info("Fetching USE stocks from afx.kwayisi.org/use/")
        html = await self._fetch_with_retry(USE_URL)
        return self._parse_stock_table(html, exchange="USE")

    # ── HTTP layer ───────────────────────────────────────────────────────────

    async def _fetch_with_retry(self, url: str) -> str:
        """
        Fetch URL with retry + exponential back-off.
        Raises httpx.HTTPError after MAX_RETRIES exhausted.
        """
        last_exc: Optional[Exception] = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                await self._rate_limit()
                async with httpx.AsyncClient(
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                    follow_redirects=True,
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    logger.debug(
                        "Fetched %s — %d bytes (attempt %d)",
                        url, len(response.text), attempt,
                    )
                    return response.text

            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                last_exc = exc
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "Fetch attempt %d/%d failed for %s: %s — retrying in %.1fs",
                    attempt, MAX_RETRIES, url, exc, delay,
                )
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(delay)

        logger.error("All %d fetch attempts failed for %s", MAX_RETRIES, url)
        raise last_exc  # type: ignore[misc]

    async def _rate_limit(self) -> None:
        """Enforce minimum gap between outbound requests."""
        async with self._lock:
            import time
            now   = time.monotonic()
            gap   = now - self._last_request_at
            if gap < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - gap)
            self._last_request_at = time.monotonic()

    # ── Parsing ──────────────────────────────────────────────────────────────

    def _parse_stock_table(self, html: str, exchange: str) -> List[Dict]:
        """
        Parse afx.kwayisi.org stock table.

        Expected columns (afx format):
            Symbol | Name | Price | Change | %Change | Volume | Market Cap

        Handles:
          - Missing volume (thin markets, no-trade days)
          - Price formatted with commas (e.g. "1,234.50")
          - Change column as signed float or "--"
          - Missing rows / malformed cells
        """
        soup    = BeautifulSoup(html, "lxml")
        results: List[Dict] = []

        # afx.kwayisi.org uses a single main table
        table = soup.find("table")
        if not table:
            logger.warning("No table found in %s response — page structure may have changed", exchange)
            return results

        rows = table.find_all("tr")
        if not rows:
            return results

        # Detect header to find column positions dynamically
        header_row  = rows[0]
        header_cols = [th.text.strip().lower() for th in header_row.find_all(["th", "td"])]
        logger.debug("%s header columns: %s", exchange, header_cols)

        # Map column names to indices — graceful fallback to positional
        col_idx = self._map_columns(header_cols)

        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue  # skip empty / section-header rows

            try:
                entry = self._parse_row(cols, col_idx, exchange)
                if entry:
                    results.append(entry)
            except Exception as exc:  # noqa: BLE001
                # Never crash on a single malformed row
                logger.debug("Skipping malformed row: %s", exc)
                continue

        logger.info("Parsed %d %s records", len(results), exchange)
        return results

    def _map_columns(self, headers: List[str]) -> Dict[str, int]:
        """
        Map semantic column names to indices.
        Falls back to positional defaults if headers differ.
        """
        defaults = {
            "symbol": 0,
            "name":   1,
            "close":  2,
            "change": 3,
            "change_pct": 4,
            "volume": 5,
            "market_cap": 6,
        }
        mapping: Dict[str, int] = {}

        keyword_map = {
            "symbol": ["symbol", "ticker", "code"],
            "name":   ["name", "company", "security"],
            "close":  ["price", "close", "last"],
            "change": ["change", "chg"],
            "change_pct": ["%change", "%chg", "change%", "pct"],
            "volume": ["volume", "vol", "shares"],
            "market_cap": ["market cap", "mktcap", "cap"],
        }

        for field, keywords in keyword_map.items():
            for idx, header in enumerate(headers):
                if any(kw in header for kw in keywords):
                    mapping[field] = idx
                    break
            if field not in mapping:
                mapping[field] = defaults[field]

        return mapping

    def _parse_row(
        self, cols: list, col_idx: Dict[str, int], exchange: str
    ) -> Optional[Dict]:
        """Parse a single table row into a stock dict."""

        def text(idx: int) -> str:
            if idx >= len(cols):
                return ""
            return cols[idx].text.strip()

        def parse_float(s: str) -> Optional[float]:
            s = s.replace(",", "").replace("KES", "").replace("UGX", "").strip()
            if not s or s in ("-", "--", "N/A", "n/a"):
                return None
            try:
                return float(s)
            except ValueError:
                return None

        def parse_int(s: str) -> Optional[int]:
            s = s.replace(",", "").strip()
            if not s or s in ("-", "--"):
                return None
            try:
                return int(float(s))
            except ValueError:
                return None

        symbol = text(col_idx["symbol"]).upper()
        if not symbol or len(symbol) > 10:
            return None  # skip non-symbol rows (headers embedded in body etc.)

        name        = text(col_idx["name"]) or symbol
        close       = parse_float(text(col_idx["close"]))
        change      = parse_float(text(col_idx.get("change", 3)))
        change_pct  = parse_float(text(col_idx.get("change_pct", 4)))
        volume      = parse_int(text(col_idx.get("volume", 5)))
        market_cap  = parse_float(text(col_idx.get("market_cap", 6)))

        if close is None or close <= 0:
            return None  # price is the single mandatory field

        # Data quality flags
        warning: Optional[str] = None
        if volume is None or volume == 0:
            warning = "no_trades"
        elif volume < 100:
            warning = "very_low_volume"

        return {
            "symbol":                symbol,
            "name":                  name,
            "exchange":              exchange,
            "close":                 close,
            "change":                change,
            "change_pct":            change_pct,
            "volume":                volume,
            "market_cap":            market_cap,
            "date":                  date.today().isoformat(),
            "source":                "afx.kwayisi.org",
            "data_quality_warning":  warning,
            "scraped_at":            datetime.utcnow().isoformat(),
        }

    # ── Validation ───────────────────────────────────────────────────────────

    def validate(self, records: List[Dict]) -> List[Dict]:
        """
        Post-scrape validation layer:
          - Drop records with close <= 0 (should be caught in parsing but belt+braces)
          - Flag volume == 0 as no-trade day
          - Flag extreme single-day returns (>40%) for manual review
          - Return only valid records; log drops
        """
        valid:   List[Dict] = []
        dropped: int        = 0

        for r in records:
            close = r.get("close", 0)

            if not close or close <= 0:
                dropped += 1
                logger.debug("Dropped %s: invalid close price %s", r.get("symbol"), close)
                continue

            # Volume flag already set in parsing; re-apply if somehow missing
            if r.get("volume") == 0 and not r.get("data_quality_warning"):
                r["data_quality_warning"] = "no_trades"

            # Flag extreme moves for downstream anomaly detection
            chg_pct = r.get("change_pct")
            if chg_pct is not None and abs(chg_pct) > 40:
                r["data_quality_warning"] = "extreme_move"
                logger.info(
                    "Extreme move flagged — %s: %.1f%%", r["symbol"], chg_pct
                )

            valid.append(r)

        if dropped:
            logger.warning("Validation dropped %d records", dropped)

        logger.info(
            "Validated %d/%d %s records",
            len(valid), len(valid) + dropped,
            records[0].get("exchange", "?") if records else "?",
        )
        return valid


# ── Module-level singleton ───────────────────────────────────────────────────

scraper = NSEScraper()