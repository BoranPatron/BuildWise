from fastapi import APIRouter

from . import auth, users, projects, tasks, documents, milestones, quotes, messages, gdpr, cost_positions, buildwise_fees, geo, finance_analytics

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(documents.router)
api_router.include_router(milestones.router)
api_router.include_router(quotes.router)
api_router.include_router(messages.router)
api_router.include_router(gdpr.router)
api_router.include_router(cost_positions.router)
api_router.include_router(buildwise_fees.router)
api_router.include_router(geo.router)
api_router.include_router(finance_analytics.router)
