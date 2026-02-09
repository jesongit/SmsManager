"""Device management API routes."""
from datetime import datetime
from typing import List
import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.device import Device
from app.models.user import User
from app.schemas.device import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceListResponse,
    DeviceTestResponse,
    DeviceTestRequest,
    ScanResponse,
)
from app.schemas.sf import (
    SMSSendRequest,
    SMSQueryRequest,
    CallQueryRequest,
    ContactQueryRequest,
    ContactAddRequest,
    WOLRequest,
    ClonePullRequest,
)
from app.utils.auth import get_current_user
from app.utils.network import discover_devices
from app.services.sf_service import SmsForwarderClient


router = APIRouter(tags=["Devices"])


# ============== Device List ==============

@router.get("", response_model=DeviceListResponse)
async def list_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List all devices (battery fetched separately by frontend)."""
    devices = db.query(Device).offset(skip).limit(limit).all()
    total = db.query(Device).count()

    # Return devices without battery (frontend fetches battery in real-time)
    result_devices = []
    for d in devices:
        result_devices.append(DeviceResponse(
            id=d.id,
            name=d.name,
            ip=d.ip,
            port=d.port,
            remark=d.remark,
            api_version=d.api_version,
            last_seen=d.last_seen,
            battery_level=None,  # Frontend fetches this separately
            created_at=d.created_at,
        ))

    return DeviceListResponse(
        devices=result_devices,
        total=total,
    )


# ============== Get Battery for All Devices ==============

@router.get("/batteries")
async def get_all_batteries(db: Session = Depends(get_db)):
    """Get battery status for all devices in real-time (concurrent query)."""
    import asyncio
    from app.services.sf_service import SmsForwarderClient

    devices = db.query(Device).all()

    async def query_single_device(d: Device):
        """Query battery for a single device."""
        try:
            client = SmsForwarderClient(d.ip, d.port, None)
            # Use short timeout for faster failure detection
            battery = await asyncio.wait_for(
                client.query_battery(),
                timeout=2.0  # 2 seconds timeout
            )
            return {
                "device_id": d.id,
                "battery_level": battery.level,
                "plugged": battery.plugged in ['AC', 'USB', 'wireless'],
                "online": True,
            }
        except asyncio.TimeoutError:
            # Timeout - device likely offline
            return {
                "device_id": d.id,
                "battery_level": None,
                "plugged": False,
                "online": False,
            }
        except Exception:
            # Connection error - device offline
            return {
                "device_id": d.id,
                "battery_level": None,
                "plugged": False,
                "online": False,
            }

    # Query all devices concurrently
    tasks = [query_single_device(d) for d in devices]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions and return valid results
    final_results = []
    for r in results:
        if isinstance(r, dict):
            final_results.append(r)

    return {"devices": final_results}


# ============== Network Scanning ==============

@router.post("/scan", response_model=ScanResponse)
async def scan_network():
    """
    Scan local network for devices using ARP cache and port probing.

    Scanning Strategy:
    - Ports: 5000 (SmsForwarder), 80 (HTTP), 443 (HTTPS), 8080 (Alt HTTP)
    - Concurrency: 200 simultaneous connections
    - Timeout: 0.1 seconds per port
    - Range: First 50 IPs in local network

    Returns:
        Discovered devices with ARP cache and scanned results
    """
    return await discover_devices()


# ============== Test ==============

@router.post("/test", response_model=DeviceTestResponse)
async def test_device_by_ip(test_data: DeviceTestRequest):
    """Test connection to a device by IP and port (before adding)."""
    client = SmsForwarderClient(
        test_data.ip,
        test_data.port,
        None,  # No API key for initial test
    )

    success, message, api_version = await client.test_connection()

    return DeviceTestResponse(
        success=success,
        message=message,
        api_version=api_version,
    )


# ============== Create Device ==============

@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
async def create_device(
    device_data: DeviceCreate,
    db: Session = Depends(get_db),
):
    """Add a new device."""
    device = Device(
        name=device_data.name,
        ip=device_data.ip,
        port=device_data.port,
        remark=device_data.remark,
        api_version=device_data.api_version,
        api_key=device_data.api_key,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


# ============== Device by ID ==============

@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: int, db: Session = Depends(get_db)):
    """Get device by ID."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    db: Session = Depends(get_db),
):
    """Update a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )

    update_data = device_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(device, field, value)

    db.commit()
    db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, db: Session = Depends(get_db)):
    """Delete a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )
    db.delete(device)
    db.commit()


@router.post("/test/{device_id}", response_model=DeviceTestResponse)
async def test_device(device_id: int, db: Session = Depends(get_db)):
    """Test connection to a device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="设备不存在"
        )

    client = SmsForwarderClient(
        device.ip,
        device.port,
        device.api_key,
    )

    success, message, api_version = await client.test_connection()

    # Update last_seen if successful
    if success:
        device.last_seen = datetime.utcnow()
        if api_version and not device.api_version:
            device.api_version = api_version
        db.commit()

    return DeviceTestResponse(
        success=success,
        message=message,
        api_version=api_version or device.api_version,
    )


# ============== SmsForwarder API Proxy ==============

@router.post("/{device_id}/sms/send")
async def send_sms(
    device_id: int,
    sms_data: SMSSendRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send SMS through device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    result = await client.send_sms(
        sms_data.sim_slot,
        sms_data.phone_numbers,
        sms_data.msg_content,
    )
    return result


@router.post("/{device_id}/sms/query")
async def query_sms(
    device_id: int,
    query_data: SMSQueryRequest,
    db: Session = Depends(get_db),
):
    """Query SMS messages from device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    messages = await client.query_sms(
        query_data.type,
        query_data.page_num,
        query_data.page_size,
        query_data.keyword,
    )
    return {"messages": [m.model_dump() for m in messages]}


@router.post("/{device_id}/call/query")
async def query_calls(
    device_id: int,
    query_data: CallQueryRequest,
    db: Session = Depends(get_db),
):
    """Query call logs from device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    calls = await client.query_calls(
        query_data.type,
        query_data.page_num,
        query_data.page_size,
        query_data.phone_number,
    )
    return {"calls": [c.model_dump() for c in calls]}


@router.post("/{device_id}/contact/query")
async def query_contacts(
    device_id: int,
    query_data: ContactQueryRequest,
    db: Session = Depends(get_db),
):
    """Query contacts from device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    contacts = await client.query_contacts(
        query_data.phone_number,
        query_data.name,
    )
    return {"contacts": [c.model_dump() for c in contacts]}


@router.post("/{device_id}/contact/add")
async def add_contact(
    device_id: int,
    contact_data: ContactAddRequest,
    db: Session = Depends(get_db),
):
    """Add contact to device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    result = await client.add_contact(
        contact_data.phone_number,
        contact_data.name,
    )
    return result


@router.post("/{device_id}/battery")
async def query_battery(device_id: int, db: Session = Depends(get_db)):
    """Query battery status from device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    battery = await client.query_battery()
    return battery.model_dump()


@router.post("/{device_id}/location")
async def query_location(device_id: int, db: Session = Depends(get_db)):
    """Query location from device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    try:
        location = await client.query_location()
        location_dict = location.model_dump()
        # Check if all location values are null
        if not any(location_dict.get(k) for k in ["address", "latitude", "longitude", "provider", "time"]):
            location_dict["error"] = "设备未开启定位功能或定位失败"
        return location_dict
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 500:
            return {"address": None, "latitude": None, "longitude": None, "provider": None, "time": None, "error": "设备未开启定位功能或定位失败"}
        raise


@router.post("/{device_id}/wol")
async def send_wol(
    device_id: int,
    wol_data: WOLRequest,
    db: Session = Depends(get_db),
):
    """Send WOL packet."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    result = await client.send_wol(wol_data.mac, wol_data.ip, wol_data.port)
    return result


@router.post("/{device_id}/clone/pull")
async def pull_config(
    device_id: int,
    pull_data: ClonePullRequest,
    db: Session = Depends(get_db),
):
    """Pull configuration from device."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    result = await client.pull_config(pull_data.version_code)
    return result


@router.post("/{device_id}/config")
async def get_device_config(device_id: int, db: Session = Depends(get_db)):
    """Get device configuration."""
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")

    client = SmsForwarderClient(device.ip, device.port, device.api_key)
    config = await client.get_config()
    return config
