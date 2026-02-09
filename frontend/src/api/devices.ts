import api from './index'

// Types
export interface Device {
  id: number
  name: string
  ip: string
  port: number
  remark: string | null
  api_version: string
  last_seen: string | null
  battery_level: number | null
  created_at: string
}

export interface DeviceCreate {
  name: string
  ip: string
  port?: number
  remark?: string
  api_version?: string
  api_key?: string
}

export interface ScannedDevice {
  ip: string
  hostname: string
  port: number
  is_smsforwarder: boolean
  response_time: number
  device_info?: Record<string, unknown>
  battery_level?: number | null
  battery_plugged?: boolean
  battery_online?: boolean
}

export interface NetworkDevice {
  ip: string
  mac?: string
  hostname: string
  interface?: string
  port?: number
  is_smsforwarder?: boolean
}

export interface ScanResult {
  local_ip: string
  gateway_ip: string
  arp_devices: NetworkDevice[]
  scanned_devices: ScannedDevice[]
  total_arp: number
  total_scanned: number
  message: string
}

export interface SMSItem {
  name: string | null
  number: string
  content: string
  date: string
  type: number
  sim_id: string | null
  sub_id: string | null
}

export interface CallItem {
  name: string | null
  number: string
  date_long: number
  duration: number
  type: number
  sim_id: string | null
}

export interface ContactItem {
  name: string
  phone_number: string
}

export interface BatteryStatus {
  level: number
  scale: number
  voltage: number
  temperature: number
  status: string
  health: string
  plugged: string
}

export interface DeviceBattery {
  device_id: number
  battery_level: number | null
  plugged: boolean  // 是否充电中
  online: boolean
}

export interface LocationInfo {
  address: string | null
  latitude: string | null
  longitude: string | null
  provider: string | null
  time: string | null
  error?: string
}

export interface DeviceConfig {
  version_code: number
  version_name: string
  device_mark: string
  sim1_carrier: string
  sim1_number: string
  sim2_carrier: string
  sim2_number: string
  enable_api_v3: boolean
  enable_api_sms_send: boolean
  enable_api_sms_query: boolean
  enable_api_call_query: boolean
  enable_api_contact_query: boolean
  enable_api_contact_add: boolean
  enable_api_location: boolean
  enable_api_battery_query: boolean
  enable_api_wol: boolean
  enable_api_clone: boolean
}

// Device APIs
export const deviceApi = {
  async list(skip = 0, limit = 100): Promise<{ devices: Device[]; total: number }> {
    const response = await api.get('/devices', { params: { skip, limit } })
    return response.data
  },

  async get(id: number): Promise<Device> {
    const response = await api.get<Device>(`/devices/${id}`)
    return response.data
  },

  async create(data: DeviceCreate): Promise<Device> {
    const response = await api.post<Device>('/devices', data)
    return response.data
  },

  async update(id: number, data: Partial<DeviceCreate>): Promise<Device> {
    const response = await api.put<Device>(`/devices/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await api.delete(`/devices/${id}`)
  },

  async scan(localIp?: string): Promise<ScanResult> {
    const params = localIp ? { local_ip: localIp } : {}
    const response = await api.post<ScanResult>('/devices/scan', {}, { params })
    return response.data
  },

  // Get battery status for all devices (real-time)
  async getAllBatteries(): Promise<{ devices: DeviceBattery[] }> {
    const response = await api.get('/devices/batteries')
    return response.data
  },

  async test(id: number): Promise<{ success: boolean; message: string; api_version: string | null }> {
    const response = await api.post(`/devices/test/${id}`)
    return response.data
  },

  async testByIP(ip: string, port: number): Promise<{ success: boolean; message: string; api_version: string | null }> {
    const response = await api.post('/devices/test', { ip, port })
    return response.data
  },

  // SMS
  async sendSMS(id: number, simSlot: number, phoneNumbers: string, content: string): Promise<unknown> {
    return api.post(`/devices/${id}/sms/send`, {
      sim_slot: simSlot,
      phone_numbers: phoneNumbers,
      msg_content: content
    })
  },

  async querySMS(id: number, type: number, pageNum: number, pageSize: number, keyword?: string): Promise<{ messages: SMSItem[] }> {
    const response = await api.post(`/devices/${id}/sms/query`, {
      type,
      page_num: pageNum,
      page_size: pageSize,
      keyword
    })
    return response.data
  },

  // Calls
  async queryCalls(id: number, type: number, pageNum: number, pageSize: number, phoneNumber?: string): Promise<{ calls: CallItem[] }> {
    const response = await api.post(`/devices/${id}/call/query`, {
      type,
      page_num: pageNum,
      page_size: pageSize,
      phone_number: phoneNumber
    })
    return response.data
  },

  // Contacts
  async queryContacts(id: number, phoneNumber?: string, name?: string): Promise<{ contacts: ContactItem[] }> {
    const response = await api.post(`/devices/${id}/contact/query`, {
      phone_number: phoneNumber,
      name: name
    })
    return response.data
  },

  async addContact(id: number, phoneNumber: string, name?: string): Promise<unknown> {
    return api.post(`/devices/${id}/contact/add`, {
      phone_number: phoneNumber,
      name
    })
  },

  // Battery
  async queryBattery(id: number): Promise<BatteryStatus> {
    const response = await api.post<BatteryStatus>(`/devices/${id}/battery`)
    return response.data
  },

  // Location
  async queryLocation(id: number): Promise<LocationInfo> {
    const response = await api.post<LocationInfo>(`/devices/${id}/location`)
    return response.data
  },

  // WOL
  async sendWOL(id: number, mac: string, ip?: string, port = 9): Promise<unknown> {
    return api.post(`/devices/${id}/wol`, { mac, ip, port })
  },

  // Config
  async getConfig(id: number): Promise<DeviceConfig> {
    const response = await api.post<DeviceConfig>(`/devices/${id}/config`)
    return response.data
  },

  // Clone
  async pullConfig(id: number, versionCode: number): Promise<unknown> {
    return api.post(`/devices/${id}/clone/pull`, { version_code: versionCode })
  }
}
