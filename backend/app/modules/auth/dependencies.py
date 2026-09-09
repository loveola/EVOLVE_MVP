import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.modules.auth.schemas import UserResponse
from datetime import datetime, timezone

security = HTTPBearer()

_jwks_client = None

def get_jwks_client():
    global _jwks_client
    if _jwks_client is None and settings.SUPABASE_JWKS_URL:
        _jwks_client = jwt.PyJWKClient(settings.SUPABASE_JWKS_URL)
    return _jwks_client

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserResponse:
    token = credentials.credentials
    jwks = get_jwks_client()
    
    if not (jwks or settings.SUPABASE_JWT_SECRET):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Neither SUPABASE_JWKS_URL nor SUPABASE_JWT_SECRET is configured."
        )

    try:
        if jwks:
            signing_key = jwks.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                options={"verify_aud": False}
            )
        else:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject identifier.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_metadata = payload.get("user_metadata") or {}
        app_metadata = payload.get("app_metadata") or {}
        is_admin = (
            payload.get("role") == "admin"
            or app_metadata.get("role") == "admin"
            or app_metadata.get("is_admin") is True
        )

        return UserResponse(
            uid=user_id,
            email=payload.get("email"),
            display_name=user_metadata.get("full_name"),
            is_active=True,
            is_admin=is_admin,
            created_at=datetime.now(timezone.utc)
        )
    except (jwt.PyJWTError, Exception) as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Supabase session token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_admin(
    current_user: UserResponse = Depends(get_current_user)
) -> UserResponse:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required.",
        )
    return current_user

