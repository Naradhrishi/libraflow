from fastapi import APIRouter, Depends, HTTPException, status
import uuid
from fastapi.security import OAuth2PasswordBearer
from app.db import AsyncSession, get_session
from typing import Annotated
from sqlmodel import select
from app.models import User, UserResponse
from app.core import decode_jwt_token
import jwt


router = APIRouter(tags=["users"])

token_extractor = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.get("/me", response_model=UserResponse)
async def me(token : Annotated[str, Depends(token_extractor)], async_session: Annotated[AsyncSession, Depends(get_session)]):

    decoded_token: dict = decode_jwt_token(token)
    # Check token type, because only access token is valid here in this endpoint
    if decoded_token.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")

    query = select(User).where(User.id == decoded_token.get("sub"), User.is_active == True)
    user = (await async_session.exec(query)).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found or has been deactivated!")

    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(user_id: uuid.UUID, async_session: Annotated[AsyncSession, Depends(get_session)], token : Annotated[str, Depends(token_extractor)]):
    decoded_token = decode_jwt_token(token)
    is_active_admin = (await async_session.exec(select(User).where(User.id == decoded_token.get("sub"), User.role == "admin", User.is_active == True))).first()
    if is_active_admin is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden! Admin access required or account deactivated.")

    # if he/she passes that test that means, he/she is an admin and can access.
    user = (await async_session.exec(select(User).where(User.id == user_id, User.is_active == True))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User does not exist or deactivated!")
    return user

