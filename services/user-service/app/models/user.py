from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from enum import Enum
import uuid
from datetime import datetime
from sqlalchemy import TIMESTAMP, func


class UserRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class UserBase(SQLModel):
    full_name: str = Field(nullable = False, max_length = 100)
    email: EmailStr = Field(unique = True, index = True, max_length = 100)
    phone: str | None = Field(default = None, max_length = 15)
    role: UserRole = Field(nullable = False, default = UserRole.MEMBER)
    is_active: bool = Field(nullable = False, default = True)


class User(UserBase, table = True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory = uuid.uuid4, primary_key = True, unique = True, nullable = False, index = True)
    hashed_password: str = Field(nullable = False)
    created_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": func.now()},
    )

    updated_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True),
        nullable=False,
        sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()},
    )



class UserCreate(UserBase):
    password: str = Field(nullable = False, min_length = 8, max_length = 20)


class UserLogin(SQLModel):
    email: EmailStr = Field(nullable = False, max_length = 100)
    password: str = Field(nullable = False, min_length = 8, max_length = 20)


class UserResponse(UserBase): # This is basically UserRead, what a user can fetch from table
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime





