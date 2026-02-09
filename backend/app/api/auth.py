"""Authentication API routes."""
import os
import uuid
from datetime import timedelta
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from PIL import Image

from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserLogin,
    UserResponse,
    UserUpdate,
    UserPasswordUpdate,
    Token,
    TOTPSetupResponse,
    TOTPVerifyRequest,
)
from app.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from app.utils.totp import (
    generate_secret,
    generate_qr_code_data_url,
    verify_totp,
)
from app.config import settings


router = APIRouter(tags=["Authentication"])


# 注册功能已移除，仅允许默认 admin 用户登录
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    totp_code: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Login and get access token.

    Args:
        form_data: Username and password
        totp_code: Optional TOTP code for 2FA
        db: Database session

    Returns:
        JWT access token

    Raises:
        HTTPException: If credentials invalid
    """
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check TOTP if enabled
    if user.totp_enabled:
        if not totp_code:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请输入两步验证码",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not verify_totp(user.totp_secret, totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="验证码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token = create_access_token(
        data={"sub": user.username}
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout():
    """Logout (client-side token removal)."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile."""
    if user_data.username:
        # Check if new username is taken
        existing = db.query(User).filter(
            User.username == user_data.username,
            User.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被占用"
            )
        current_user.username = user_data.username

    if user_data.avatar:
        current_user.avatar = user_data.avatar

    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password")
async def update_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user password."""
    old_password = password_data.validated_old_password
    new_password = password_data.validated_new_password

    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )

    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    return {"message": "密码修改成功"}


# ============== TOTP 2FA Routes ==============

@router.post("/2fa/setup", response_model=TOTPSetupResponse)
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Setup TOTP 2FA for current user.

    Returns:
        Secret key and QR code data URL
    """
    if current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两步验证已启用"
        )

    secret = generate_secret()
    qr_code = generate_qr_code_data_url(
        secret=secret,
        username=current_user.username,
        issuer=settings.totp_issuer
    )

    # Save secret to database (will be enabled after verification)
    current_user.totp_secret = secret
    db.commit()

    return TOTPSetupResponse(secret=secret, qr_code=qr_code)


@router.post("/2fa/verify")
async def verify_2fa(
    request: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verify and enable TOTP 2FA.
    """
    if current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两步验证已启用"
        )

    if not current_user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请先设置两步验证"
        )

    if not verify_totp(current_user.totp_secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )

    # Enable 2FA
    current_user.totp_enabled = True
    db.commit()

    return {"message": "两步验证已启用"}


@router.post("/2fa/disable")
async def disable_2fa(
    request: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disable TOTP 2FA.
    """
    if not current_user.totp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两步验证未启用"
        )

    if not verify_totp(current_user.totp_secret, request.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="验证码错误"
        )

    # Disable 2FA
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()

    return {"message": "两步验证已禁用"}


@router.get("/2fa/status")
async def get_2fa_status(current_user: User = Depends(get_current_user)):
    """Get current user's 2FA status."""
    return {
        "enabled": current_user.totp_enabled,
        "secret_set": current_user.totp_secret is not None
    }


# ============== Avatar Upload Route ==============

AVATAR_DIR = Path(settings.database_file).parent / "avatars"
AVATAR_DIR.mkdir(exist_ok=True)


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload and crop user avatar.

    Accepts a square image and automatically crops it to 200x200,
    then compresses and saves as PNG.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的文件格式，仅支持 JPEG、PNG、GIF 和 WebP"
        )

    try:
        # Open and process image
        image = Image.open(file.file)

        # Convert to RGB if necessary (for PNG with transparency)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        # Crop to square (use center)
        min_dim = min(image.width, image.height)
        left = (image.width - min_dim) // 2
        top = (image.height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        image = image.crop((left, top, right, bottom))

        # Resize to 200x200
        image = image.resize((200, 200), Image.Resampling.LANCZOS)

        # Generate unique filename
        filename = f"{current_user.username}_{uuid.uuid4().hex[:8]}.png"
        filepath = AVATAR_DIR / filename

        # Save with compression (quality=85 gives good balance)
        image.save(filepath, "PNG", optimize=True, quality=85)

        # Delete old avatar if exists
        old_avatar = current_user.avatar
        if old_avatar and old_avatar.startswith("/avatars/"):
            old_filename = old_avatar.split("/")[-1]
            old_filepath = AVATAR_DIR / old_filename
            if old_filepath.exists():
                try:
                    old_filepath.unlink()
                except OSError:
                    pass  # Ignore deletion errors

        # Update user avatar URL
        avatar_url = f"/avatars/{filename}"
        current_user.avatar = avatar_url
        db.commit()

        return {"avatar_url": avatar_url}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理图片失败: {str(e)}"
        )


@router.delete("/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete user avatar."""
    old_avatar = current_user.avatar
    if old_avatar and old_avatar.startswith("/avatars/"):
        filename = old_avatar.split("/")[-1]
        filepath = AVATAR_DIR / filename
        if filepath.exists():
            try:
                filepath.unlink()
            except OSError:
                pass

    current_user.avatar = None
    db.commit()

    return {"message": "Avatar deleted successfully"}
