"""User Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


# ============== User Schemas ==============

class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    avatar: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    """Schema for updating password."""
    old_password: Optional[str] = None
    oldPassword: Optional[str] = None
    new_password: str = Field(..., min_length=6, max_length=100)
    newPassword: Optional[str] = Field(None, min_length=6, max_length=100)

    @model_validator(mode='before')
    @classmethod
    def normalize_fields(cls, data):
        if isinstance(data, dict):
            # Handle camelCase to snake_case conversion
            if 'oldPassword' in data and 'old_password' not in data:
                data['old_password'] = data.pop('oldPassword')
            if 'newPassword' in data and 'new_password' not in data:
                data['new_password'] = data.pop('newPassword')
        return data

    @property
    def validated_old_password(self) -> str:
        return self.old_password or ""

    @property
    def validated_new_password(self) -> str:
        return self.new_password or self.newPassword or ""


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    avatar: Optional[str]
    totp_enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for login request."""
    username: str
    password: str
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6)


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TOTPSetupResponse(BaseModel):
    """Schema for TOTP setup response."""
    secret: str
    qr_code: str  # Data URL


class TOTPVerifyRequest(BaseModel):
    """Schema for TOTP verification."""
    code: str = Field(..., min_length=6, max_length=6)
