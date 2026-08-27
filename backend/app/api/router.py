"""
Main API router — aggregates all endpoint routers under /api prefix.

Todos os endpoints /api/* exigem um Bearer JWT válido emitido pelo CRM_MG
(ver app/auth.py). O health-check fica em app/main.py, fora deste router, e
continua público.
"""

from fastapi import APIRouter, Depends

from app.auth import get_crm_user
from app.api.endpoints import (
    confidential,
    expectations,
    overview,
    presentation,
    roles,
    salary,
    tenure,
    benefits,
)

router = APIRouter(prefix="/api", dependencies=[Depends(get_crm_user)])

router.include_router(confidential.router)
router.include_router(overview.router)
router.include_router(expectations.router)
router.include_router(salary.router)
router.include_router(tenure.router)
router.include_router(roles.router)
router.include_router(presentation.router)
router.include_router(benefits.router)
