# > hash_password(), verify_password(), create_access_token(), decode_token()
from pwdlib import PasswordHash
from app.core import settings
from fastapi.concurrency import run_in_threadpool
import jwt # pywjt 
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status

password_hash = PasswordHash.recommended()

async def async_hash_password(password: str) -> str:
    return await run_in_threadpool(password_hash.hash, password)


async def async_verify_password(password: str,  hashed_password: str) -> bool:
    return await run_in_threadpool(password_hash.verify, password, hashed_password)

'''
payload should look like this 
{
  "sub": "3f9a9827364y9sdk1c2e-...-uuid",
  "role": "member/admin",
  "type": "access/refresh",
  "exp": 1735689900
}
'''

def create_access_token(data: dict):
    # create the access token here to implement jwt in login system
    payload_to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload_to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt_token = jwt.encode(payload_to_encode, settings.secret_key, algorithm=settings.jwt_encode_algo)
    return encoded_jwt_token

def create_refresh_token(data: dict):
    # create the access token here to implement jwt in login system
    payload_to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.refresh_token_expire_minutes)
    payload_to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt_token = jwt.encode(payload_to_encode, settings.secret_key, algorithm=settings.jwt_encode_algo)
    return encoded_jwt_token

# '''Solved : This function may throw an exception; handle it from where you are calling it'''
def decode_jwt_token(encoded_jwt_token: str) -> dict:
    try:
        payload = jwt.decode(encoded_jwt_token, settings.secret_key, algorithms=[settings.jwt_encode_algo])

        if payload.get("type") != "access" and payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type!")
        if payload.get("role") != "member" and payload.get("role") != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user type token payload!")
        if not payload.get("sub"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload!")

        return payload
    
    except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token expired!")
            
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format.")
        
    except Exception as e:
        print(f"Unexpected token error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server verification error.")
    



