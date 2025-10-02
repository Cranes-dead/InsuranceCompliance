"""
API v1 router that combines all endpoint routers.
"""

from fastapi import APIRouter

from .endpoints import compliance, documents, health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(health.router, prefix="/system", tags=["system"])