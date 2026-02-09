"""Device Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ============== Device Schemas ==============

class DeviceBase(BaseModel):
    """Base device schema."""
    name: str = Field(..., min_length=1, max_length=100)
    ip: str = Field(..., pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    port: int = Field(default=5000, ge=1, le=65535)


class DeviceCreate(DeviceBase):
    """Schema for creating a device."""
    remark: Optional[str] = None
    api_version: str = Field(default="v3", pattern=r'^(v2|v3)$')
    api_key: Optional[str] = None


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    remark: Optional[str] = None
    api_version: Optional[str] = Field(None, pattern=r'^(v2|v3)$')
    api_key: Optional[str] = None


class DeviceResponse(DeviceBase):
    """Schema for device response."""
    id: int
    remark: Optional[str]
    api_version: str
    last_seen: Optional[datetime]
    battery_level: Optional[int]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceListResponse(BaseModel):
    """Schema for device list response."""
    devices: list[DeviceResponse]
    total: int


class DeviceTestResponse(BaseModel):
    """Schema for device connection test."""
    success: bool
    message: str
    api_version: Optional[str] = None


class DeviceTestRequest(BaseModel):
    """Schema for testing device connection by IP and port."""
    ip: str = Field(..., pattern=r'^(\d{1,3}\.){3}\d{1,3}$')
    port: int = Field(default=5000, ge=1, le=65535)


class ScannedDeviceResponse(BaseModel):
    """Schema for a scanned device response."""
    ip: str
    hostname: str
    port: int
    is_smsforwarder: bool
    response_time: float
    device_info: Optional[dict] = None
    battery_level: Optional[int] = None
    battery_plugged: bool = False
    battery_online: bool = False

    model_config = ConfigDict(populate_by_name=True, exclude_none=False)


class ScanResponse(BaseModel):
    """Schema for network scan response."""
    local_ip: str
    gateway_ip: str = ""
    arp_devices: list = Field(default_factory=list)
    scanned_devices: list[ScannedDeviceResponse]
    total_arp: int = 0
    total_scanned: int = 0
    message: str = ""
