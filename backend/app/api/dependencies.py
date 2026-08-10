from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from app.core.config import Settings, get_settings
security=HTTPBearer()
def current_user(credentials: HTTPAuthorizationCredentials=Depends(security), settings: Settings=Depends(get_settings)) -> str:
    try: return str(jwt.decode(credentials.credentials,settings.jwt_secret_key,algorithms=["HS256"])["sub"])
    except Exception as exc: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token") from exc
