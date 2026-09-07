from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from app.db import AsyncSession, get_session
from typing import Annotated
from app.models import User, UserCreate, UserResponse, UserLogin
from sqlmodel  import select
from app.core import async_hash_password, async_verify_password, create_access_token, create_refresh_token, decode_jwt_token
import jwt
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer

token_extractor = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

router = APIRouter(
                   tags=["auth"]
                   )


@router.post("/signup", response_model=UserResponse)
async def signup(data : UserCreate, async_session: Annotated[AsyncSession, Depends(get_session)], token: Annotated[str, Depends(token_extractor)]):
    # First check here that logged in user is either an admin or not? Because only admin user can create new users
    decoded_token: dict =  decode_jwt_token(token)
    # As only access token based user is allowed at this endpoint
    if decoded_token.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type!")
    # check either user is admin or not? Only admin is allowed to create new users.
    if decoded_token.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user! You are not authorize to create new users!")

    existing_user = (await async_session.exec(select(User).where(User.email == data.email))).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists! Please try another email."
        )

    # If wanna change privilege of a user from Admin to Member or vice versa then do check it from database here then move forward.
    # Verify from DB here first, as of now I am not using it because as of now there is no option for privilege change in this software.
    # code here

    # MUST FIX: check admin is active or not then allow.
    is_active_admin = (await async_session.exec(select(User).where(User.id == decoded_token.get("sub"), User.role == "admin", User.is_active == True))).first()
    if is_active_admin is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden! Admin access required or account deactivated.")


    # user does not exist here so 
    curr_hashed_password = await async_hash_password(data.password)

    new_user = User(
        full_name = data.full_name,
        email = data.email,
        phone = data.phone,
        role = data.role,
        is_active = data.is_active,
        hashed_password = curr_hashed_password
    )

    async_session.add(new_user)
    await async_session.commit()
    await async_session.refresh(new_user)

    return new_user


@router.post("/login")
async def login(data: Annotated[OAuth2PasswordRequestForm, Depends()], async_session: Annotated[AsyncSession, Depends(get_session)], response: Response):
    query = select(User).where(User.email == data.username, User.is_active == True)
    signed_up = (await async_session.exec(query)).first()

    if not signed_up or not await async_verify_password(data.password, signed_up.hashed_password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail="Invalid user id or password!")
    # if he signed up and has verify password then send him access token and refresh token as well
    user_id: str = str(signed_up.id)
    payload = {"sub": user_id, "role": signed_up.role}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    response.set_cookie(key="refresh_token", value=refresh_token, max_age=2592000, secure=True, httponly=True, samesite="lax")

    return {
            "message" : "Successfully logged in !",
            "access_token" : access_token,
            "token_type" : "bearer"
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", secure=True, httponly=True, samesite="lax")
    # and also, don't forget to delete the access token ont front end site as well.
    return {"Message" : "Successfully logged out and cookie deleted"}


@router.post("/refresh")
async def refresh(response: Response, async_session: Annotated[AsyncSession, Depends(get_session)], refresh_token: str | None = Cookie(default = None)):
    if not refresh_token:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = "Refresh token expired! Please log in again!")

    # If you are having the refresh token then decode it here and check either valid or not?
    payload = decode_jwt_token(refresh_token)

    # check this user is either active or not?
    user = (await async_session.exec(select(User).where(User.id == payload.get("sub"), User.is_active == True))).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated. Contact Admin")
    # if everything goes well and verified then regenerate access_token and rotate refresh token
    new_payload = {"sub": str(payload.get("sub")), "role": str(payload.get("role"))}

    new_access_token = create_access_token(new_payload)
    new_refresh_token = create_refresh_token(new_payload)
    response.set_cookie(key="refresh_token", value=new_refresh_token, max_age=2592000, secure=True, httponly=True, samesite="lax")

    return {
        "access_token" : new_access_token,
        "token_type" : "bearer"
    }

                        
