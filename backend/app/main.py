from fastapi import FastAPI
from app.core.config import settings
from app.modules.auth.router import router as auth_router

def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs"
    )
    
    @application.get(f"{settings.API_PREFIX}/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION
        }
        
    application.include_router(auth_router, prefix=settings.API_PREFIX)
    return application

app = create_application()
