import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Device, NetworkDevice, ScannedDevice, DeviceBattery } from '@/api/devices'
import { deviceApi } from '@/api/devices'

// Battery cache duration: 1 minute
const BATTERY_CACHE_DURATION = 60 * 1000
const BATTERY_CACHE_KEY = 'sms_manager_battery_cache'

interface BatteryCache {
  time: number
  devices: Record<number, DeviceBattery>
}

function getCachedBatteries(): BatteryCache | null {
  try {
    const cached = localStorage.getItem(BATTERY_CACHE_KEY)
    if (cached) {
      return JSON.parse(cached)
    }
  } catch (e) {
    console.error('Failed to read battery cache:', e)
  }
  return null
}

function saveBatteryCache(devices: Map<number, DeviceBattery>) {
  try {
    const obj: Record<number, DeviceBattery> = {}
    devices.forEach((value, key) => { obj[key] = value })
    localStorage.setItem(BATTERY_CACHE_KEY, JSON.stringify({
      time: Date.now(),
      devices: obj
    }))
  } catch (e) {
    console.error('Failed to save battery cache:', e)
  }
}

export const useDeviceStore = defineStore('devices', () => {
  const devices = ref<Device[]>([])
  const total = ref(0)
  const loading = ref(false)
  const currentDevice = ref<Device | null>(null)
  const batteryLevels = ref<Map<number, DeviceBattery>>(new Map())
  const batteryLoading = ref(false)

  // Check if battery cache is valid (persistent)
  function isBatteryCacheValid(): boolean {
    const cached = getCachedBatteries()
    if (!cached) return false
    return Date.now() - cached.time < BATTERY_CACHE_DURATION
  }

  // Load cached batteries from localStorage
  function loadCachedBatteries(): void {
    const cached = getCachedBatteries()
    if (cached && cached.devices) {
      const newMap = new Map<number, DeviceBattery>()
      Object.entries(cached.devices).forEach(([key, value]) => {
        newMap.set(Number(key), value)
      })
      batteryLevels.value = newMap
    }
  }

  async function fetchDevices() {
    loading.value = true
    try {
      const response = await deviceApi.list()
      devices.value = response.devices
      total.value = response.total
    } finally {
      loading.value = false
    }
  }

  // Fetch battery levels with caching (persistent)
  async function fetchBatteries(forceRefresh = false): Promise<void> {
    if (devices.value.length === 0) return

    // Load cached data first for instant display
    if (batteryLevels.value.size === 0) {
      loadCachedBatteries()
    }

    // If cache is still valid and not forcing refresh, skip API call
    if (!forceRefresh && isBatteryCacheValid()) {
      return
    }

    // Force refresh or cache expired, fetch from API
    batteryLoading.value = true
    try {
      const response = await deviceApi.getAllBatteries()
      // Update battery levels map
      const newMap = new Map<number, DeviceBattery>()
      for (const item of response.devices) {
        newMap.set(item.device_id, item)
      }
      batteryLevels.value = newMap
      saveBatteryCache(newMap)  // Save to localStorage
    } catch (e) {
      console.error('Failed to fetch batteries:', e)
    } finally {
      batteryLoading.value = false
    }
  }

  // Force refresh battery cache
  async function refreshBatteries(): Promise<void> {
    // Ensure loading state is visible for a moment
    batteryLoading.value = true
    await new Promise(resolve => setTimeout(resolve, 300))
    await fetchBatteries(true)
  }

  // Get battery for a specific device
  function getBattery(deviceId: number): DeviceBattery | undefined {
    return batteryLevels.value.get(deviceId)
  }

  // Cache battery data from scan results (instant display without API call)
  function cacheBatteryFromScan(deviceId: number, battery: DeviceBattery): void {
    batteryLevels.value.set(deviceId, battery)
    saveBatteryCache(batteryLevels.value)
    console.log('Battery cached from scan for device', deviceId, ':', battery.battery_level, '%')
  }

  async function fetchDevice(id: number) {
    loading.value = true
    try {
      currentDevice.value = await deviceApi.get(id)
      return currentDevice.value
    } finally {
      loading.value = false
    }
  }

  async function addDevice(data: Partial<Device>) {
    const device = await deviceApi.create(data as any)
    devices.value.push(device)
    total.value++
    return device
  }

  async function updateDevice(id: number, data: Record<string, unknown>) {
    const device = await deviceApi.update(id, data as any)
    const index = devices.value.findIndex(d => d.id === id)
    if (index !== -1) {
      devices.value[index] = device
    }
    if (currentDevice.value?.id === id) {
      currentDevice.value = device
    }
    return device
  }

  async function removeDevice(id: number) {
    await deviceApi.delete(id)
    devices.value = devices.value.filter(d => d.id !== id)
    total.value--
    batteryLevels.value.delete(id)
    saveBatteryCache(batteryLevels.value)
  }

  async function scanNetwork(localIp?: string): Promise<{ arp_devices: NetworkDevice[]; scanned_devices: ScannedDevice[]; local_ip: string }> {
    const response = await deviceApi.scan(localIp)
    // Support both 'scanned_devices' (new) and 'devices' (legacy) field names
    const scannedDevices = response.scanned_devices || []
    return {
      arp_devices: response.arp_devices || [],
      scanned_devices: scannedDevices,
      local_ip: response.local_ip || ''
    }
  }

  async function testDevice(id: number) {
    return await deviceApi.test(id)
  }

  async function testDeviceByIP(ip: string, port: number) {
    return await deviceApi.testByIP(ip, port)
  }

  return {
    devices,
    total,
    loading,
    currentDevice,
    batteryLevels,
    batteryLoading,
    fetchDevices,
    fetchBatteries,
    refreshBatteries,
    isBatteryCacheValid,
    loadCachedBatteries,
    getBattery,
    cacheBatteryFromScan,
    fetchDevice,
    addDevice,
    updateDevice,
    removeDevice,
    scanNetwork,
    testDevice,
    testDeviceByIP
  }
})
