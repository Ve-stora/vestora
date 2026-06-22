"""
Vestora API Router Registry
============================
Mounts all sub-routers under /api prefix.
Import `router` in main.py and call app.include_router(router).
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api")


def _register_routers():
    from .auth      import router as auth_router
    from .market    import router as market_router
    from .portfolio import router as portfolio_router
    from .analytics import router as analytics_router
    from .b2b       import router as b2b_router

    router.include_router(auth_router,      prefix="/auth",      tags=["auth"])
    router.include_router(market_router,    prefix="/market",    tags=["market"])
    router.include_router(portfolio_router,                      tags=["portfolio"])
    router.include_router(analytics_router, prefix="/ai",        tags=["analytics"])
    router.include_router(b2b_router,       prefix="/b2b",       tags=["b2b"])


_register_routers()