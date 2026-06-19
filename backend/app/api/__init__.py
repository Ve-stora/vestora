from fastapi import APIRouter

router = APIRouter(prefix="/api")


def _register_routers():
    from .market import router as market_router
    from .portfolio import router as portfolio_router
    from .analytics import router as analytics_router

    router.include_router(market_router)
    router.include_router(portfolio_router)
    router.include_router(analytics_router)


_register_routers()