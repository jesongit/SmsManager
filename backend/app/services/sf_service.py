"""SmsForwarder API client service."""
import time
import hashlib
import httpx
from typing import Optional, Any
from app.schemas.sf import (
    SFConfigResponse,
    SMSItem,
    CallItem,
    ContactItem,
    BatteryResponse,
    LocationResponse,
)


class SmsForwarderClient:
    """Client for communicating with SmsForwarder devices."""

    def __init__(self, ip: str, port: int = 5000, api_key: Optional[str] = None):
        """
        Initialize the SmsForwarder client.

        Args:
            ip: Device IP address
            port: SmsForwarder port (default 5000)
            api_key: Optional API key for authenticated requests
        """
        self.base_url = f"http://{ip}:{port}"
        self.api_key = api_key

    async def _request(self, endpoint: str, data: dict) -> dict:
        """
        Make a request to the SmsForwarder API.

        Args:
            endpoint: API endpoint (e.g., '/sms/send')
            data: Request data (will be wrapped in {"data": ...} for v3 API)

        Returns:
            Response JSON (already extracted from {"data": ...} wrapper)

        Raises:
            HTTPException: If request fails
        """
        url = f"{self.base_url}{endpoint}"

        # Wrap data in {"data": {...}} for v3 API
        request_data = {"data": data}

        # Add timestamp and sign if API key is set
        if self.api_key:
            request_data['timestamp'] = int(time.time() * 1000)
            sign_data = ''.join(f"{k}{request_data[k]}" for k in sorted(request_data.keys()))
            request_data['sign'] = hashlib.md5(f"{sign_data}{self.api_key}".encode()).hexdigest()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=request_data)
            response.raise_for_status()
            result = response.json()

            # Extract from {"data": {...}} wrapper or return list directly
            if isinstance(result, dict) and 'data' in result:
                return result['data']
            return result

    # ============== Config ==============

    async def get_config(self) -> dict:
        """Query device configuration."""
        result = await self._request('/config/query', {})
        data = result if isinstance(result, dict) else {}

        # SIM 卡信息
        sim_info = data.get('sim_info_list', {})
        sim1_info = sim_info.get('0', {})
        sim2_info = sim_info.get('1', {})

        return {
            # 版本信息
            'version_code': data.get('version_code', 0),
            'version_name': data.get('version_name', ''),
            'device_mark': data.get('extra_device_mark', ''),
            # SIM 卡信息
            'sim1_carrier': sim1_info.get('carrier_name', ''),
            'sim1_number': sim1_info.get('number', ''),
            'sim2_carrier': sim2_info.get('carrier_name', ''),
            'sim2_number': sim2_info.get('number', ''),
            # API 开关状态
            'enable_api_v3': data.get('enable_api_v3', False),
            'enable_api_sms_send': data.get('enable_api_sms_send', False),
            'enable_api_sms_query': data.get('enable_api_sms_query', False),
            'enable_api_call_query': data.get('enable_api_call_query', False),
            'enable_api_contact_query': data.get('enable_api_contact_query', False),
            'enable_api_contact_add': data.get('enable_api_contact_add', False),
            'enable_api_location': data.get('enable_api_location', False),
            'enable_api_battery_query': data.get('enable_api_battery_query', False),
            'enable_api_wol': data.get('enable_api_wol', False),
            'enable_api_clone': data.get('enable_api_clone', False),
        }

    # ============== SMS ==============

    async def send_sms(self, sim_slot: int, phone_numbers: str, msg_content: str) -> dict:
        """
        Send SMS.

        Args:
            sim_slot: SIM slot (1 or 2)
            phone_numbers: Semicolon-separated phone numbers
            msg_content: Message content

        Returns:
            Response data
        """
        return await self._request('/sms/send', {
            'sim_slot': sim_slot,
            'phone_numbers': phone_numbers,
            'msg_content': msg_content,
        })

    async def query_sms(self, sms_type: int, page_num: int, page_size: int,
                        keyword: Optional[str] = None) -> list[SMSItem]:
        """
        Query SMS messages.

        Args:
            sms_type: Message type (1=received, 2=sent)
            page_num: Page number
            page_size: Page size
            keyword: Optional search keyword

        Returns:
            List of SMS items
        """
        data = {
            'type': sms_type,
            'page_num': page_num,
            'page_size': page_size,
        }
        if keyword:
            data['keyword'] = keyword

        result = await self._request('/sms/query', data)
        messages = result if isinstance(result, list) else []

        return [
            SMSItem(
                name=msg.get('name'),
                number=msg.get('number', ''),
                content=msg.get('content', ''),
                date=str(msg.get('date', '')),
                type=msg.get('type', 0),
                sim_id=str(msg.get('sim_id', '')),
                sub_id=str(msg.get('sub_id', '')),
            )
            for msg in messages
        ]

    # ============== Calls ==============

    async def query_calls(self, call_type: int, page_num: int, page_size: int,
                          phone_number: Optional[str] = None) -> list[CallItem]:
        """
        Query call logs.

        Args:
            call_type: Call type (0=all, 1=incoming, 2=outgoing, 3=missed)
            page_num: Page number
            page_size: Page size
            phone_number: Optional phone number filter

        Returns:
            List of call items
        """
        data = {
            'type': call_type,
            'page_num': page_num,
            'page_size': page_size,
        }
        if phone_number:
            data['phone_number'] = phone_number

        result = await self._request('/call/query', data)
        calls = result if isinstance(result, list) else []

        return [
            CallItem(
                name=call.get('name'),
                number=call.get('number', ''),
                date_long=call.get('dateLong', 0),
                duration=call.get('duration', 0),
                type=call.get('type', 0),
                sim_id=str(call.get('sim_id', '')),
            )
            for call in calls
        ]

    # ============== Contacts ==============

    async def query_contacts(self, phone_number: Optional[str] = None,
                            name: Optional[str] = None) -> list[ContactItem]:
        """
        Query contacts.

        Args:
            phone_number: Optional phone number filter
            name: Optional name filter

        Returns:
            List of contact items
        """
        data = {}
        if phone_number:
            data['phone_number'] = phone_number
        if name:
            data['name'] = name

        result = await self._request('/contact/query', data)
        contacts = result if isinstance(result, list) else []

        return [
            ContactItem(
                name=contact.get('name', ''),
                phone_number=contact.get('phone_number', ''),
            )
            for contact in contacts
        ]

    async def add_contact(self, phone_number: str, name: Optional[str] = None) -> dict:
        """
        Add a contact.

        Args:
            phone_number: Phone numbers (semicolon-separated)
            name: Contact name

        Returns:
            Response data
        """
        data = {'phone_number': phone_number}
        if name:
            data['name'] = name

        return await self._request('/contact/add', data)

    # ============== Battery ==============

    def _parse_value(self, value: str, to_type: type, default: any) -> any:
        """Parse string value to specified type, handling units like %, V, ℃."""
        if value is None:
            return default
        try:
            # Remove common units
            cleaned = str(value).replace('%', '').replace('V', '').replace('℃', '').replace('C', '').strip()
            if to_type == int:
                return int(float(cleaned))
            elif to_type == float:
                return float(cleaned)
            return default
        except (ValueError, TypeError):
            return default

    async def query_battery(self) -> BatteryResponse:
        """Query battery status."""
        result = await self._request('/battery/query', {})

        level = result.get('level', '0%')
        scale = result.get('scale', '100%')
        voltage = result.get('voltage', '0V')
        temperature = result.get('temperature', '0℃')

        return BatteryResponse(
            level=self._parse_value(level, int, 0),
            scale=self._parse_value(scale, int, 100),
            voltage=self._parse_value(voltage, int, 0),
            temperature=self._parse_value(temperature, float, 0.0),
            status=result.get('status', 'unknown'),
            health=result.get('health', 'unknown'),
            plugged=result.get('plugged', 'unplugged'),
        )

    # ============== Location ==============

    async def query_location(self) -> LocationResponse:
        """Query device location."""
        result = await self._request('/location/query', {})

        return LocationResponse(
            address=result.get('address'),
            latitude=result.get('latitude'),
            longitude=result.get('longitude'),
            provider=result.get('provider'),
            time=result.get('time'),
        )

    # ============== WOL ==============

    async def send_wol(self, mac: str, ip: Optional[str] = None, port: int = 9) -> dict:
        """
        Send Wake on LAN packet.

        Args:
            mac: Target MAC address
            ip: Optional broadcast IP
            port: WOL port (default 9)

        Returns:
            Response data
        """
        data = {'mac': mac}
        if ip:
            data['ip'] = ip
        data['port'] = port

        return await self._request('/wol/send', data)

    # ============== Clone ==============

    async def pull_config(self, version_code: int) -> dict:
        """
        Pull configuration from device.

        Args:
            version_code: App version code

        Returns:
            Device configuration
        """
        return await self._request('/clone/pull', {'version_code': version_code})

    async def push_config(self, config: dict) -> dict:
        """
        Push configuration to device.

        Args:
            config: Configuration dictionary

        Returns:
            Response data
        """
        return await self._request('/clone/push', config)

    # ============== Test ==============

    async def test_connection(self) -> tuple[bool, str, Optional[str]]:
        """
        Test connection to device.

        Returns:
            Tuple of (success, message, api_version)
        """
        try:
            config = await self.get_config()
            return True, "Connection successful", "v3"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return True, "Connection successful", "v2"
            return False, f"HTTP Error: {e.response.status_code}", None
        except Exception as e:
            return False, str(e), None
