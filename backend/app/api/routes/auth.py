from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.core.config import Settings, get_settings
from app.services.auth import create_token, hash_password, verify_password
from app.services.repository import ApplicationRepository
router=APIRouter(prefix="/auth")
class Credentials(BaseModel): email:str; password:str=Field(min_length=8)
class Token(BaseModel): access_token:str; token_type:str="bearer"
@router.post("/register",response_model=Token,status_code=status.HTTP_201_CREATED)
def register(payload:Credentials,settings:Settings=Depends(get_settings))->Token:
    repo=ApplicationRepository(settings.app_database_path)
    try: user_id=repo.create_user(payload.email,hash_password(payload.password))
    except ValueError as exc: raise HTTPException(409,"Email already registered") from exc
    return Token(access_token=create_token(user_id,settings))
@router.post("/login",response_model=Token)
def login(payload:Credentials,settings:Settings=Depends(get_settings))->Token:
    user=ApplicationRepository(settings.app_database_path).get_user_by_email(payload.email)
    if not user or not verify_password(payload.password,str(user["password_hash"])): raise HTTPException(401,"Invalid email or password")
    return Token(access_token=create_token(str(user["user_id"]),settings))
