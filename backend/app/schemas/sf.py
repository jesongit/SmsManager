"""SmsForwarder API Pydantic schemas."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ============== SmsForwarder API Schemas ==============

# Config Query
class SFConfigQuery(BaseModel):
    """Request for config query."""
    data: dict = {}
    timestamp: int
    sign: Optional[str] = None


class SFConfigResponse(BaseModel):
    """Response from config query."""
    enable_api_v3: bool = False
    enable_api_rsa: bool = False
    enable_api_sm4: bool = False
    device_mark: str = ""
    sim1_mark: str = ""
    sim2_mark: str = ""


# SMS
class SMSSendRequest(BaseModel):
    """Request for sending SMS."""
    sim_slot: int = Field(ge=1, le=2)
    phone_numbers: str  # Semicolon separated
    msg_content: str


class SMSQueryRequest(BaseModel):
    """Request for querying SMS."""
    type: int = Field(ge=1, le=2)  # 1=received, 2=sent
    page_num: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    keyword: Optional[str] = None


class SMSItem(BaseModel):
    """SMS item."""
    name: Optional[str]
    number: str
    content: str
    date: str
    type: int
    sim_id: Optional[str]
    sub_id: Optional[str]


class SMSQueryResponse(BaseModel):
    """Response for SMS query."""
    messages: List[SMSItem]


# Call
class CallQueryRequest(BaseModel):
    """Request for querying calls."""
    type: int = Field(ge=0, le=3)  # 0=no filter, 1=incoming, 2=outgoing, 3=missed
    page_num: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    phone_number: Optional[str] = None


class CallItem(BaseModel):
    """Call item."""
    name: Optional[str]
    number: str
    date_long: int
    duration: int
    type: int
    sim_id: Optional[str]


class CallQueryResponse(BaseModel):
    """Response for call query."""
    calls: List[CallItem]


# Contact
class ContactQueryRequest(BaseModel):
    """Request for querying contacts."""
    phone_number: Optional[str] = None
    name: Optional[str] = None


class ContactItem(BaseModel):
    """Contact item."""
    name: str
    phone_number: str


class ContactQueryResponse(BaseModel):
    """Response for contact query."""
    contacts: List[ContactItem]


class ContactAddRequest(BaseModel):
    """Request for adding contact."""
    phone_number: str  # Semicolon separated
    name: Optional[str] = None


# Battery
class BatteryResponse(BaseModel):
    """Battery status response."""
    level: int
    scale: int
    voltage: int
    temperature: float
    status: str  # charging, discharging, full, not_charging, unknown
    health: str
    plugged: str  # ac, usb, unplugged


# Location
class LocationResponse(BaseModel):
    """Location response."""
    address: Optional[str]
    latitude: Optional[str]
    longitude: Optional[str]
    provider: Optional[str]
    time: Optional[str]


# WOL
class WOLRequest(BaseModel):
    """Wake on LAN request."""
    mac: str = Field(..., pattern=r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$')
    ip: Optional[str] = None
    port: int = Field(default=9, ge=1, le=65535)


# Clone
class ClonePullRequest(BaseModel):
    """Request for pulling config from device."""
    version_code: int


class ClonePushRequest(BaseModel):
    """Request for pushing config to device."""
    version_name: str
    version_code: int
    sender_list: list
    rule_list: list


class CloneResponse(BaseModel):
    """Response for clone operation."""
    success: bool
    config: Optional[dict] = None
    message: str = ""
