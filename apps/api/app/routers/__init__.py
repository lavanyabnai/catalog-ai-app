from fastapi import APIRouter, Depends

from app.core.auth import get_current_user
from app.routers import assets, brand_kits, bundles, categories, jobs, personas, products, tryon

api_router = APIRouter(prefix="/api/v1", dependencies=[Depends(get_current_user)])
api_router.include_router(products.router)
api_router.include_router(assets.router)
api_router.include_router(brand_kits.router)
api_router.include_router(categories.router)
api_router.include_router(jobs.router)
api_router.include_router(bundles.router)
api_router.include_router(personas.router)
api_router.include_router(tryon.router)
