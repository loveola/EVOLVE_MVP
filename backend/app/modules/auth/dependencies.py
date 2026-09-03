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
    
    try:
        if jwks:
            signing_key = jwks.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256", "HS256"],
                options={"verify_aud": False}
            )
        elif settings.SUPABASE_JWT_SECRET:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Neither SUPABASE_JWKS_URL nor SUPABASE_JWT_SECRET is configured."
            )

        user_metadata = payload.get("user_metadata") or {}
        return UserResponse(
            uid=payload.get("sub"),
            email=payload.get("email"),
            display_name=user_metadata.get("full_name"),
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired Supabase session: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
