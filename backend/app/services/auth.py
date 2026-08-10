"""Password hashing and JWT authentication helpers."""
import hashlib, hmac, os
from datetime import UTC, datetime, timedelta
import jwt
from app.core.config import Settings

def hash_password(password: str) -> str:
    salt=os.urandom(16); digest=hashlib.pbkdf2_hmac("sha256",password.encode(),salt,200_000)
    return f"{salt.hex()}${digest.hex()}"
def verify_password(password: str, value: str) -> bool:
    salt,digest=value.split("$",1); actual=hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),200_000).hex()
    return hmac.compare_digest(actual,digest)
def create_token(user_id: str, settings: Settings) -> str:
    return jwt.encode({"sub":user_id,"exp":datetime.now(UTC)+timedelta(minutes=settings.jwt_expire_minutes)},settings.jwt_secret_key,algorithm="HS256")
