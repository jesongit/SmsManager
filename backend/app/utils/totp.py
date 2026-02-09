"""TOTP (Time-based One-Time Password) utilities."""
import io
import base64
from typing import Tuple
import pyotp
import qrcode


def generate_secret() -> str:
    """Generate a new TOTP secret key."""
    return pyotp.random_base32()


def generate_qr_code_data_url(secret: str, username: str, issuer: str) -> str:
    """
    Generate a QR code data URL for TOTP setup.

    Args:
        secret: The TOTP secret key
        username: User's username
        issuer: App/Service name

    Returns:
        Data URL containing the QR code image
    """
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name=issuer
    )

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 data URL
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


def verify_totp(secret: str, code: str) -> bool:
    """
    Verify a TOTP code.

    Args:
        secret: The TOTP secret key
        code: The 6-digit code to verify

    Returns:
        True if the code is valid, False otherwise
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)  # Allow 1 step tolerance


def get_current_totp(secret: str) -> str:
    """Get the current TOTP code (for testing purposes)."""
    totp = pyotp.TOTP(secret)
    return totp.now()
