"""Network utilities for device discovery and ARP scanning."""
import asyncio
import socket
import subprocess
import re
import time
import json
import httpx
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

# 扫描配置
FAST_SCAN_TIMEOUT = 0.5  # 快速 TCP 端口检测超时
HTTP_TIMEOUT = 1.0  # HTTP 请求超时
VERIFY_TIMEOUT = 1.0  # API 验证超时
BATTERY_TIMEOUT = 1.0  # 电量查询超时


@dataclass
class DiscoveredDevice:
    """扫描发现的设备。"""
    ip: str
    hostname: str = ""
    port: int = 0
    is_smsforwarder: bool = False
    response_time: float = 0
    device_info: Optional[Dict[str, Any]] = None
    battery_level: Optional[int] = None
    battery_plugged: bool = False
    battery_online: bool = False

    def to_dict(self) -> dict:
        """转换为字典（包含电量信息）。"""
        return {
            'ip': self.ip,
            'hostname': self.hostname,
            'port': self.port,
            'is_smsforwarder': self.is_smsforwarder,
            'response_time': self.response_time,
            'device_info': self.device_info,
            'battery_level': self.battery_level,
            'battery_plugged': self.battery_plugged,
            'battery_online': self.battery_online,
        }


async def get_local_ip() -> str:
    """获取本机 IP 地址，通过路由探测获取真实用于外网的 IP。"""
    # 首先检查环境变量（支持手动配置）
    import os
    manual_ip = os.environ.get('LOCAL_IP')
    if manual_ip:
        return manual_ip

    # 方法1：使用 ip route get 获取真正用于外网通信的源 IP
    try:
        result = subprocess.run(
            ['ip', 'route', 'get', '1.1.1.1'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # 解析输出找到源 IP
            # 典型输出: "1.1.1.1 via 192.168.31.1 dev eth0 src 192.168.31.20 ..."
            match = re.search(r'src\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                src_ip = match.group(1)
                # 排除 Docker 虚拟网络 IP
                if not src_ip.startswith(('172.', '192.168.65.', '192.168.66.', '100.')):
                    return src_ip
    except Exception:
        pass

    # 方法2：尝试连接外部地址来检测源 IP
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(('8.8.8.8', 80))
        src_ip = sock.getsockname()[0]
        sock.close()
        if not src_ip.startswith(('172.', '192.168.65.', '192.168.66.', '100.')):
            return src_ip
    except Exception:
        pass

    # 方法3：回退到 hostname -I，但过滤掉虚拟 IP
    try:
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            ips = result.stdout.strip().split()
            # 排除 Docker/WinNAT 虚拟网络 IP
            exclude_prefixes = (
                '172.16.', '172.17.', '172.18.', '172.19.',
                '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
                '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
                '172.30.', '172.31.',
                '192.168.65.', '192.168.66.',  # WSL2/Docker WinNAT
                '192.168.122.',  # libvirt
                '100.',  # Docker 保留地址
            )
            for ip in ips:
                if not any(ip.startswith(prefix) for prefix in exclude_prefixes):
                    return ip
            # 如果都是虚拟 IP，返回第一个非 localhost 的
            for ip in ips:
                if not ip.startswith('127.'):
                    return ip
            return ips[0] if ips else "192.168.1.1"
    except Exception:
        pass

    return "192.168.1.1"


def _sync_port_scan(ip: str, port: int, timeout: float) -> bool:
    """同步 TCP 端口检测（在线程池中执行）。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, port))
        return True
    except (socket.timeout, OSError):
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


async def batch_fast_scan(ips: List[str], port: int = 5000) -> List[str]:
    """批量快速端口扫描（使用线程池执行器）。"""
    from concurrent.futures import ThreadPoolExecutor

    def _scan_all():
        # 使用 50 并发，0.5 秒超时
        with ThreadPoolExecutor(max_workers=50) as executor:
            results = list(executor.map(
                lambda ip: _sync_port_scan(ip, port, FAST_SCAN_TIMEOUT),
                ips
            ))
        return [ip for ip, result in zip(ips, results) if result]

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _scan_all)


async def check_port(ip: str, port: int = 5000) -> bool:
    """检测端口是否开放并验证是否为 SmsForwarder 设备（使用 httpx）。"""
    for attempt in range(2):  # 重试一次
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                response = await client.post(f"http://{ip}:{port}/config/query", json={"data": {}})
                if response.status_code == 200:
                    data = response.json()
                    # 检查是否为 SmsForwarder 设备
                    if 'data' in data and isinstance(data['data'], dict):
                        if data['data'].get('version_code'):
                            return True
                return False
        except Exception:
            if attempt == 1:  # 第二次失败才退出
                return False
            await asyncio.sleep(0.1)  # 重试前短暂等待
    return False


async def verify_device(ip: str, port: int = 5000) -> Optional[Dict[str, Any]]:
    """验证设备是否是 SmsForwarder 并获取配置信息（使用 httpx）。"""
    url = f"http://{ip}:{port}/config/query"
    payload = {"data": {}}

    try:
        async with httpx.AsyncClient(timeout=VERIFY_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
    except Exception:
        pass
    return None


async def query_battery(ip: str, port: int = 5000) -> Optional[Dict[str, Any]]:
    """获取设备电量信息（使用 httpx）。"""
    url = f"http://{ip}:{port}/battery/query"
    payload = {"data": {}}

    try:
        async with httpx.AsyncClient(timeout=BATTERY_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    return data['data']
                return data if isinstance(data, dict) else None
    except Exception:
        pass
    return None


async def get_device_info(ip: str, port: int = 5000) -> Dict[str, Any]:
    """获取设备完整信息（包含电量）。"""
    config = await verify_device(ip, port)
    if not config:
        return {}

    result = dict(config)

    # 尝试获取电量信息
    battery = await query_battery(ip, port)
    if battery:
        # 解析电量数据（level 可能是 "85%" 这样的字符串）
        level_str = battery.get('level', '0%')
        try:
            level = int(level_str.replace('%', '').strip()) if level_str else None
        except (ValueError, AttributeError):
            level = None

        plugged = battery.get('plugged', '')
        is_plugged = plugged in ['AC', 'USB', 'wireless', 'charging']

        result['battery'] = {
            'level': level,
            'plugged': is_plugged
        }
    else:
        result['battery'] = {'level': None, 'plugged': False}

    return result


async def scan_network(network_prefix: str) -> List[DiscoveredDevice]:
    """扫描网络中的 SmsForwarder 设备（两阶段扫描优化）。"""
    devices: List[DiscoveredDevice] = []

    # 生成所有要扫描的 IP
    all_ips = [f"{network_prefix}.{i}" for i in range(1, 256)]

    print(f"🔍 扫描 {network_prefix}.x...")

    # 第一阶段：快速 TCP 端口检测（0.3 秒超时）
    print("  📡 第一阶段：快速端口检测...")
    # 直接扫描所有 IP
    potential_ips = await batch_fast_scan(all_ips)
    print(f"  📡 快速扫描完成，找到 {len(potential_ips)} 个开放端口")

    if not potential_ips:
        return []

    # 第二阶段：验证 SmsForwarder 设备并获取信息
    print("  📡 第二阶段：验证设备并获取信息...")
    info_tasks = [get_device_info(ip) for ip in potential_ips]
    info_results = await asyncio.gather(*info_tasks, return_exceptions=True)

    for ip, info in zip(potential_ips, info_results):
        # 只处理返回有效配置信息的设备（SmsForwarder）
        if isinstance(info, dict) and info.get('version_code'):
            # 获取电量信息
            battery = info.get('battery', {})
            battery_level = battery.get('level')
            battery_plugged = battery.get('plugged', False)

            # 获取主机名（优先使用 device_mark/extra_device_mark，其次 DNS 反解）
            # device_mark 是 API 返回的设备名称，更准确
            hostname = info.get('device_mark', '') or info.get('extra_device_mark', '')
            if not hostname:
                try:
                    hostname = socket.gethostbyaddr(ip)[0].split('.')[0]
                except Exception:
                    hostname = f"device-{ip.split('.')[-1]}"

            # 确保主机名不为空且合理
            if not hostname or hostname.startswith('127.') or hostname == ip:
                hostname = info.get('device_mark', '') or f"device-{ip.split('.')[-1]}"

            devices.append(DiscoveredDevice(
                ip=ip,
                hostname=hostname,
                port=5000,
                is_smsforwarder=True,
                device_info=info,
                battery_level=battery_level,
                battery_plugged=battery_plugged,
                battery_online=True
            ))
            print(f"  ✅ {ip} - {hostname} (电量: {battery_level}%)")
        else:
            # 非 SmsForwarder 设备
            print(f"  ⚠️ {ip} - 非 SmsForwarder 设备")

    devices.sort(key=lambda d: d.ip)
    return devices


async def discover_devices(manual_local_ip: str = None) -> Dict[str, Any]:
    """发现网络中的 SmsForwarder 设备。"""
    start_time = time.time()

    # 如果前端传入了本机 IP，优先使用
    if manual_local_ip:
        local_ip = manual_local_ip
        print(f"📍 使用前端指定的本机 IP: {local_ip}")
    else:
        local_ip = await get_local_ip()
        print(f"📍 自动检测到本机 IP: {local_ip}")

    # ✅ 修复：提取网段前缀
    network_prefix = ".".join(local_ip.split('.')[:3])
    print(f"🔍 扫描网段: {network_prefix}.x")

    devices = await scan_network(network_prefix)
    elapsed = time.time() - start_time

    print(f"\n⏱️ 扫描完成，用时 {elapsed:.1f} 秒")

    return {
        'local_ip': local_ip,
        'gateway_ip': '',
        'arp_devices': [],
        'scanned_devices': [d.to_dict() for d in devices],
        'total_arp': 0,
        'total_scanned': len(devices),
        'message': f'找到 {len(devices)} 个设备 (用时 {elapsed:.1f}秒)'
    }
