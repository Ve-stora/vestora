"""
Analytics Service — LLM Layer
==============================
Builds market context from DB, calls Groq/OpenAI-compatible API,
enforces data-vendor framing on every response.
"""

import json
from typing import Dict, Optional

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.market import get_anomalies, get_stocks
from app.utils.framing import DISCLAIMER, wrap_analytics

# Exported so api/analytics.py can pass it through without duplicating
SYSTEM_PROMPT = """
You are Vestora's market analytics engine for East African capital markets,
primarily the Nairobi Securities Exchange (NSE).

You analyze market data and provide data-driven insights.

STRICT RULES — never violate these:
1. Never tell users to buy, sell, or hold any security.
2. Never provide personalized investment advice.
3. Frame ALL outputs as data observations:
   - "The data shows..."
   - "Historically, this pattern..."
   - "The model indicates..."
   - "Market data suggests..."
4. When asked for a recommendation: "I can show what the data indicates,
   but investment decisions should be made with a licensed financial advisor."
5. Always cite the data source and note it is end-of-day NSE data.
6. You cover NSE equities and bonds. Phase 2 will add USE (Uganda).
7. Keep responses concise and data-focused.
"""


async def run_analytics_query(
    query: str,
    context: Optional[Dict],
    system_prompt: str,
    db: AsyncSession,
) -> Dict:
    """
    Build market context, call LLM, return framed response.
    Falls back gracefully if LLM API key not configured.
    """
    if not settings.LLM_API_KEY:
        return {
            "answer": (
                "Analytics engine not configured. "
                "Add LLM_API_KEY to your .env file (Groq is free at console.groq.com)."
            ),
            "disclaimer": DISCLAIMER,
            "sources": [],
        }

    market_context = await _build_market_context(db, context)

    client = AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Current market context:\n{market_context}"},
        {"role": "user",   "content": query},
    ]

    try:
        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=messages,
            max_tokens=600,
            temperature=0.3,
        )
        raw_answer = response.choices[0].message.content or ""
        return wrap_analytics(raw_answer)

    except Exception as e:
        return {
            "answer":     f"Analytics engine error: {str(e)}",
            "disclaimer": DISCLAIMER,
            "sources":    [],
            "error":      str(e),
        }


async def _build_market_context(db: AsyncSession, extra: Optional[Dict] = None) -> str:
    """Build a compact market context string for the LLM."""
    try:
        stocks    = await get_stocks(db, exchange="NSE")
        anomalies = await get_anomalies(db, exchange="NSE", days=3)

        top_stocks = sorted(
            [s for s in stocks if s.get("change_pct") is not None],
            key=lambda x: abs(x.get("change_pct", 0)),
            reverse=True,
        )[:5]

        context_lines = ["NSE Market Snapshot (end-of-day):"]
        for s in top_stocks:
            chg = s.get("change_pct", 0) or 0
            context_lines.append(
                f"  {s['symbol']}: KES {s['close']:.2f} ({chg:+.1f}%)"
            )

        if anomalies:
            context_lines.append("\nRecent anomalies (statistical flags only):")
            for a in anomalies[:3]:
                context_lines.append(
                    f"  {a['symbol']}: {a['anomaly_type']} (score {a['anomaly_score']:.2f})"
                )

        if extra:
            context_lines.append(f"\nAdditional context: {json.dumps(extra)}")

        return "\n".join(context_lines)

    except Exception:
        return "Market context unavailable — answer from general NSE knowledge."