from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.assessment.router import router as assessment_router
from app.modules.recommendation.router import router as recommendation_router

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs"
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get(f"{settings.API_PREFIX}/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION
        }

    application.include_router(auth_router, prefix=settings.API_PREFIX)
    application.include_router(assessment_router, prefix=settings.API_PREFIX)
    application.include_router(recommendation_router, prefix=settings.API_PREFIX)
    return application

app = create_application()
