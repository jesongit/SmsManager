<template>
  <div class="home-container">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <n-icon size="28" color="#18a058">
          <PhonePortraitOutline />
        </n-icon>
        <h1>SmsManager</h1>
      </div>
      <div class="header-right">
        <n-dropdown :options="userMenuOptions" @select="handleUserMenuSelect">
          <div class="user-avatar">
            <n-avatar
              v-if="authStore.avatar"
              :src="authStore.avatar"
              round
              :size="36"
            />
            <n-avatar v-else round :size="36" style="background-color: #18a058">
              {{ authStore.username.charAt(0).toUpperCase() }}
            </n-avatar>
          </div>
        </n-dropdown>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <n-tabs v-model:value="activeTab" type="line" animated>
        <!-- Device List Tab -->
        <n-tab-pane name="list" tab="设备列表">
          <div class="section-header">
            <div class="section-title">
              <h2>我的设备</h2>
              <n-button
                quaternary
                circle
                size="small"
                :loading="deviceStore.batteryLoading"
                @click="handleRefreshBattery"
              >
                <template #icon><n-icon><RefreshOutline /></n-icon></template>
              </n-button>
            </div>
            <n-tag type="info">{{ deviceStore.total }} 个设备</n-tag>
          </div>

          <n-spin :show="deviceStore.loading">
            <div v-if="deviceStore.devices.length === 0" class="empty-state">
              <n-empty description="暂无设备">
                <template #extra>
                  <n-button type="primary" @click="activeTab = 'add'">
                    添加设备
                  </n-button>
                </template>
              </n-empty>
            </div>

            <div v-else class="device-grid">
              <div
                v-for="device in deviceStore.devices"
                :key="device.id"
                class="device-card"
                @click="goToDevice(device.id)"
              >
                <div class="device-icon" :class="{ 'has-port': device.port }">
                  <n-icon size="32" :color="device.battery_level !== null ? getBatteryColor(device.battery_level) : '#999'">
                    <PhonePortraitOutline />
                  </n-icon>
                </div>
                <div class="device-info">
                  <h3>{{ formatDeviceName(device) }}</h3>
                  <p class="device-ip">
                    <n-icon><GlobeOutline /></n-icon>
                    {{ device.ip }}:{{ device.port }}
                  </p>
                </div>
                <div class="device-actions">
                  <!-- 电量显示 -->
                  <div v-if="getDeviceBattery(device.id)?.online" class="battery-display">
                    <div class="battery-icon" :class="getBatteryIconClass(getDeviceBattery(device.id)?.battery_level || 0, getDeviceBattery(device.id)?.plugged || false)">
                      <div class="battery-level" :style="{ width: (getDeviceBattery(device.id)?.battery_level || 0) + '%' }"></div>
                    </div>
                    <div class="battery-text">
                      <span class="battery-level-text">{{ getDeviceBattery(device.id)?.battery_level }}%</span>
                      <n-icon v-if="getDeviceBattery(device.id)?.plugged" class="charging-icon" color="#18a058">
                        <FlashOutline />
                      </n-icon>
                    </div>
                  </div>
                  <n-tag v-else type="default" size="small">
                    离线
                  </n-tag>
                  <n-button quaternary circle size="small" @click.stop="confirmDelete(device)">
                    <template #icon><n-icon><TrashOutline /></n-icon></template>
                  </n-button>
                </div>
              </div>
            </div>
          </n-spin>
        </n-tab-pane>

        <!-- Scan Tab -->
        <n-tab-pane name="scan" tab="扫描设备">
          <div class="scan-container">
            <div class="scan-header">
              <div class="scan-info">
                <h3>局域网扫描</h3>
                <p class="network-info">
                  <n-icon><WifiOutline /></n-icon>
                  本机IP:
                  <span v-if="!editingLocalIp" class="local-ip-display">
                    {{ localIp || '检测中...' }}
                    <n-button text type="primary" size="small" @click="startEditLocalIp">
                      <template #icon><n-icon><CreateOutline /></n-icon></template>
                    </n-button>
                  </span>
                  <n-input
                    v-else
                    v-model:value="editLocalIpValue"
                    placeholder="例如: 192.168.1.100"
                    size="small"
                    style="width: 150px;"
                    @keyup.enter="saveLocalIp"
                    @blur="saveLocalIp"
                  />
                </p>
              </div>
              <div class="scan-actions">
                <n-button type="primary" :loading="scanning" @click="handleScan">
                  <template #icon><n-icon><ScanOutline /></n-icon></template>
                  {{ scanning ? '扫描中...' : '开始扫描' }}
                </n-button>
                <n-button :disabled="!scanLog" @click="showScanLog">
                  <template #icon><n-icon><DocumentTextOutline /></n-icon></template>
                  日志
                </n-button>
              </div>
            </div>

            <!-- Scan Progress -->
            <n-progress
              v-if="scanning"
              type="line"
              :percentage="scanProgress"
              :show-indicator="true"
              status="success"
            />

            <!-- Scan Results -->
            <div v-if="scanResult.length > 0" class="scan-results">
              <n-divider>扫描结果 ({{ scanKnownCount }} 个已知，{{ scanNewCount }} 个新增)</n-divider>
              <div class="device-list">
                <div
                  v-for="device in scanResult"
                  :key="device.ip"
                  class="device-item"
                  :class="{ 'is-known': device.is_known, 'is-new': device.is_new }"
                >
                  <div class="device-item-icon">
                    <n-icon size="24" :color="device.is_smsforwarder ? '#18a058' : '#666'">
                      <HardwareChipOutline />
                    </n-icon>
                  </div>
                  <div class="device-item-info">
                    <div class="device-item-name">
                      {{ device.hostname || device.ip }}
                      <n-tag v-if="device.is_new" type="warning" size="tiny">新增</n-tag>
                      <n-tag v-else-if="device.is_known" type="info" size="tiny">已知</n-tag>
                    </div>
                    <div class="device-item-ip">
                      <n-icon><GlobeOutline /></n-icon>
                      {{ device.ip }}
                    </div>
                  </div>
                  <!-- 电量信息 -->
                  <div v-if="device.is_smsforwarder && device.battery_level !== null" class="scan-battery">
                    <div class="scan-battery-icon" :class="getBatteryIconClass(device.battery_level || 0, device.battery_plugged || false)">
                      <div class="battery-level" :style="{ width: (device.battery_level || 0) + '%' }"></div>
                    </div>
                    <span class="scan-battery-text">{{ device.battery_level }}%</span>
                    <n-icon v-if="device.battery_plugged" class="charging-icon" color="#18a058">
                      <FlashOutline />
                    </n-icon>
                  </div>
                </div>
              </div>
            </div>

            <n-empty v-else-if="!scanning" description="点击上方按钮开始扫描局域网">
              <template #icon>
                <n-icon size="48" color="#ccc"><SearchOutline /></n-icon>
              </template>
            </n-empty>
          </div>
        </n-tab-pane>

        <!-- Manual Add Tab -->
        <n-tab-pane name="add" tab="手动添加">
          <div class="add-container">
            <n-card title="添加设备" class="add-card">
              <n-form ref="addFormRef" :model="addForm" :rules="addRules" label-placement="top">
                <n-grid :cols="1" :x-gap="24">
                  <n-gi>
                    <n-form-item label="IP地址" path="ip">
                      <n-input v-model:value="addForm.ip" placeholder="如 192.168.1.100">
                        <template #prefix>
                          <n-icon><GlobeOutline /></n-icon>
                        </template>
                      </n-input>
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item label="端口" path="port">
                      <n-input-number v-model:value="addForm.port" :min="1" :max="65535" style="width: 100%">
                        <template #prefix>
                          <n-icon><GridOutline /></n-icon>
                        </template>
                      </n-input-number>
                    </n-form-item>
                  </n-gi>
                  <n-gi>
                    <n-form-item label="备注名">
                      <n-input v-model:value="addForm.nickname" placeholder="可选，给自己看的名字">
                        <template #prefix>
                          <n-icon><CreateOutline /></n-icon>
                        </template>
                      </n-input>
                    </n-form-item>
                  </n-gi>
                </n-grid>
              </n-form>
              <div class="add-actions">
                <n-button @click="resetForm">重置</n-button>
                <n-button type="primary" :loading="adding" @click="handleAddDevice">
                  添加设备
                </n-button>
              </div>
            </n-card>
          </div>
        </n-tab-pane>
      </n-tabs>
    </main>

    <!-- Scan Log Dialog -->
    <n-modal v-model:show="showLogDialog" preset="card" title="扫描日志" style="width: 600px; max-width: 90vw;">
      <n-spin :show="scanning">
        <n-input
          v-model:value="scanLog"
          type="textarea"
          readonly
          :rows="20"
          placeholder="暂无扫描日志，请先执行扫描"
          style="font-family: monospace; font-size: 13px; line-height: 1.6;"
        />
      </n-spin>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import {
  PhonePortraitOutline,
  ScanOutline,
  TrashOutline,
  HardwareChipOutline,
  GlobeOutline,
  GridOutline,
  SearchOutline,
  WifiOutline,
  FlashOutline,
  RefreshOutline,
  CreateOutline,
  DocumentTextOutline
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { useDeviceStore } from '@/stores/devices'
import { type ScannedDevice, deviceApi } from '@/api/devices'
import { authApi } from '@/api/auth'
import api from '@/api'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const authStore = useAuthStore()
const deviceStore = useDeviceStore()

// Tabs
const activeTab = ref('list')

// Add Device Form
const addFormRef = ref()
const adding = ref(false)
const addForm = reactive({
  ip: '',
  port: 5000,
  nickname: ''
})

const addRules = {
  ip: { required: true, message: '请输入IP地址', pattern: /^(\d{1,3}\.){3}\d{1,3}$/, trigger: 'blur' }
}

// Format device name for display
function formatDeviceName(device: { name: string; remark: string | null }): string {
  if (device.remark) {
    return `${device.remark}（${device.name}）`
  }
  return device.name
}

// Scan
const scanning = ref(false)
const scanProgress = ref(0)
const scanResult = ref<(ScannedDevice & { is_known?: boolean; is_new?: boolean })[]>([])
const localIp = ref('')
const editingLocalIp = ref(false)
const editLocalIpValue = ref('')
const scanLog = ref('')
const showLogDialog = ref(false)

// Start editing local IP
function startEditLocalIp() {
  editLocalIpValue.value = localIp.value
  editingLocalIp.value = true
}

// Save manually entered local IP
function saveLocalIp() {
  if (editLocalIpValue.value && isValidIP(editLocalIpValue.value)) {
    localIp.value = editLocalIpValue.value
    localStorage.setItem('manual_local_ip', editLocalIpValue.value)
    message.success(`本机IP已设置为: ${editLocalIpValue.value}`)
  } else {
    message.warning('请输入有效的IP地址')
  }
  editingLocalIp.value = false
}

// Show scan log dialog
function showScanLog() {
  showLogDialog.value = true
}
const scanKnownCount = computed(() => scanResult.value.filter(d => d.is_known).length)
const scanNewCount = computed(() => scanResult.value.filter(d => d.is_new).length)

// Validate IP address format
function isValidIP(ip: string): boolean {
  const ipv4Pattern = /^(\d{1,3}\.){3}\d{1,3}$/
  if (!ipv4Pattern.test(ip)) return false
  const parts = ip.split('.')
  return parts.every(part => {
    const num = parseInt(part, 10)
    return num >= 0 && num <= 255
  })
}

// Get battery color based on level
function getBatteryColor(level: number): string {
  if (level >= 80) return '#18a058'
  if (level >= 50) return '#f0a020'
  return '#d03050'
}

// Get device battery status from store
function getDeviceBattery(deviceId: number) {
  return deviceStore.getBattery(deviceId)
}

// Get battery icon class based on level and charging status
function getBatteryIconClass(level: number, plugged: boolean): string {
  const baseClass = 'battery-'
  if (plugged) {
    return baseClass + 'charging'
  }
  if (level >= 80) return baseClass + 'high'
  if (level >= 50) return baseClass + 'medium'
  if (level >= 20) return baseClass + 'low'
  return baseClass + 'critical'
}

// User Menu
const userMenuOptions = [
  { label: '个人中心', key: 'profile' },
  { type: 'divider' },
  { label: '退出登录', key: 'logout' }
]

async function handleUserMenuSelect(key: string) {
  if (key === 'profile') {
    router.push('/profile')
  } else if (key === 'logout') {
    // 忽略 API 错误，强制清理本地状态并跳转
    try {
      await authApi.logout().catch(() => {})
    } finally {
      authStore.token = null
      authStore.user = null
      localStorage.removeItem('token')
      router.push('/login')
    }
  }
}

// 获取本机IP（用于扫描显示）
async function fetchLocalIp() {
  // 优先使用手动设置的 IP
  const manualIp = localStorage.getItem('manual_local_ip')
  if (manualIp) {
    localIp.value = manualIp
    return
  }
  // 如果没有手动 IP，从后端获取
  try {
    const response = await api.post('/devices/scan')
    if (response.data.local_ip) {
      localIp.value = response.data.local_ip
    }
  } catch {
    // 静默失败，不显示错误
  }
}

async function handleAddDevice() {
  // Validate IP format first
  if (!addForm.ip) {
    message.warning('请输入IP地址')
    return
  }

  if (!isValidIP(addForm.ip)) {
    message.warning('请输入有效的IP地址')
    return
  }

  adding.value = true

  try {
    // Check for duplicate device (same IP and port)
    const exists = deviceStore.devices.some(d => d.ip === addForm.ip && d.port === addForm.port)
    if (exists) {
      message.warning('该设备已存在（相同IP和端口）')
      adding.value = false
      return
    }

    // Test connection to verify it's a valid device
    const testDevice = await deviceStore.testDeviceByIP(addForm.ip, addForm.port)
    if (!testDevice.success) {
      message.warning('无法连接到该设备，请确认IP和端口是否正确')
      adding.value = false
      return
    }

    // Use nickname as initial name, will be updated with device mark from API
    const initialName = addForm.nickname || addForm.ip
    const newDevice = await deviceStore.addDevice({
      name: initialName,
      ip: addForm.ip,
      port: addForm.port,
      remark: addForm.nickname || undefined
    })

    // Fetch device config to get actual device mark
    try {
      const config = await deviceApi.getConfig(newDevice.id)
      if (config.device_mark) {
        await deviceStore.updateDevice(newDevice.id, {
          name: config.device_mark
        })
      }
    } catch (e) {
      // Ignore if failed to fetch device mark
    }

    message.success('设备添加成功')
    activeTab.value = 'list'
    resetForm()
    await deviceStore.fetchDevices()
  } catch (error) {
    message.error('添加设备失败')
  } finally {
    adding.value = false
  }
}

function resetForm() {
  addForm.ip = ''
  addForm.port = 5000
  addForm.nickname = ''
}

async function handleScan() {
  scanning.value = true
  scanProgress.value = 0
  scanResult.value = []

  // Start building scan log
  const scanStartTime = new Date().toLocaleString('zh-CN')
  let logBuilder = `# 局域网扫描日志\n`
  logBuilder += `## 扫描信息\n`
  logBuilder += `- **扫描时间**: ${scanStartTime}\n`
  logBuilder += `- **本机IP**: ${localIp.value || '未知'}\n`
  logBuilder += `- **扫描网段**: ${localIp.value ? localIp.value.split('.').slice(0, 3).join('.') + '.x' : '未知'}\n\n`

  try {
    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      if (scanProgress.value < 90) {
        scanProgress.value += 10
      }
    }, 300)

    // 传递前端设置的本机 IP，确保后端扫描正确的网段
    const result = await deviceStore.scanNetwork(localIp.value)
    clearInterval(progressInterval)
    scanProgress.value = 100

    // Get existing device IPs for comparison
    const existingDeviceIps = new Set(deviceStore.devices.map(d => d.ip))

    // Process all scanned devices
    const scanDevices: (ScannedDevice & { is_known?: boolean; is_new?: boolean })[] = []
    let addedCount = 0
    let knownCount = 0
    let otherCount = 0

    // Group devices by type for log
    const sfDevices: string[] = []
    const otherDevices: string[] = []

    if (result.scanned_devices) {
      for (const device of result.scanned_devices) {
        const isKnown = existingDeviceIps.has(device.ip)
        const isNew = device.is_smsforwarder && !isKnown

        // Build detailed device info for log
        let deviceInfo = `### 📍 ${device.ip}\n`
        deviceInfo += `  - **主机名**: ${device.hostname || '未知'}\n`
        deviceInfo += `  - **端口**: ${device.port || 5000}\n`
        deviceInfo += `  - **响应时间**: ${device.response_time}ms\n`

        if (device.device_info && Object.keys(device.device_info).length > 0) {
          deviceInfo += `  - **设备信息**:\n`
          for (const [key, value] of Object.entries(device.device_info)) {
            deviceInfo += `    - ${key}: ${value}\n`
          }
        }

        if (device.is_smsforwarder) {
          // SmsForwarder device
          const scannedDevice = device as ScannedDevice & { is_known?: boolean }
          deviceInfo += `  - **类型**: ✅ SmsForwarder\n`
          if (scannedDevice.battery_level !== null) {
            deviceInfo += `  - **电量**: ${scannedDevice.battery_level}%\n`
            deviceInfo += `  - **充电状态**: ${scannedDevice.battery_plugged ? '🔌 充电中' : '🔋 使用电池'}\n`
            deviceInfo += `  - **在线状态**: ${scannedDevice.battery_online !== false ? '🟢 在线' : '🔴 离线'}\n`
          }
          if (scannedDevice.is_known) {
            deviceInfo += `  - **状态**: 📋 已知设备\n`
            knownCount++
          } else if (isNew) {
            deviceInfo += `  - **状态**: ✨ 新增设备\n`
            addedCount++
          }
          sfDevices.push(deviceInfo)

          scanDevices.push({
            ...device,
            is_smsforwarder: true,
            is_known: isKnown,
            is_new: isNew
          })

          // If it's a new SmsForwarder device, add it
          if (isNew) {
            try {
              const newDevice = await deviceStore.addDevice({
                name: device.hostname || device.ip,
                ip: device.ip,
                port: device.port || 5000,
                remark: ''
              })

              // Cache battery data
              if (device.battery_level != null) {
                deviceStore.cacheBatteryFromScan(newDevice.id, {
                  device_id: newDevice.id,
                  battery_level: device.battery_level || null,
                  plugged: device.battery_plugged || false,
                  online: device.battery_online !== false
                })
              }
            } catch (error: any) {
              deviceInfo += `  - **添加结果**: ❌ 添加失败: ${error.message || error}\n`
            }
          }
        } else {
          // Non-SmsForwarder device
          deviceInfo += `  - **类型**: 🌐 其他设备\n`
          deviceInfo += `  - **说明**: 未安装 SmsForwarder，无法进行管理\n`
          otherDevices.push(deviceInfo)
          otherCount++
        }
      }
    }

    // Build log content
    logBuilder += `## 📱 SmsForwarder 设备 (${sfDevices.length} 个)\n\n`
    if (sfDevices.length > 0) {
      sfDevices.forEach(d => logBuilder += `${d}\n`)
    } else {
      logBuilder += `_未发现 SmsForwarder 设备_\n`
    }

    logBuilder += `\n## 🌐 其他设备 (${otherDevices.length} 个)\n\n`
    if (otherDevices.length > 0) {
      otherDevices.forEach(d => logBuilder += `${d}\n`)
    } else {
      logBuilder += `_未发现其他设备_\n`
    }

    // Summary
    logBuilder += `\n## 📊 扫描摘要\n`
    logBuilder += `- **扫描时间**: ${scanStartTime}\n`
    logBuilder += `- **扫描网段**: ${localIp.value ? localIp.value.split('.').slice(0, 3).join('.') + '.x' : '未知'}\n`
    logBuilder += `- **SmsForwarder 设备**: ${sfDevices.length} 个 (${knownCount} 个已知，${addedCount} 个新增)\n`
    logBuilder += `- **其他设备**: ${otherDevices.length} 个\n`
    logBuilder += `- **总耗时**: ${(result as any).message?.match(/\(([\d.]+)秒\)/)?.[1] || 'N/A'}秒`

    // Save log
    scanLog.value = logBuilder

    scanResult.value = scanDevices

    // Fetch updated device list
    await deviceStore.fetchDevices()

    // Apply cached battery data
    for (const device of scanDevices) {
      if (device.is_smsforwarder && device.battery_level != null) {
        const dbDevice = deviceStore.devices.find(d => d.ip === device.ip)
        if (dbDevice) {
          deviceStore.cacheBatteryFromScan(dbDevice.id, {
            device_id: dbDevice.id,
            battery_level: device.battery_level || null,
            plugged: device.battery_plugged || false,
            online: device.battery_online !== false
          })
        }
      }
    }

    // Show summary message
    if (addedCount > 0 || knownCount > 0) {
      message.success(`扫描完成：${knownCount} 个已知，${addedCount} 个新增`)
    } else if (otherCount > 0) {
      message.info(`扫描完成：发现 ${otherCount} 个非 SmsForwarder 设备`)
    } else {
      message.info('未发现任何设备')
    }
  } catch (error: any) {
    console.error('Scan error:', error)
    message.error('扫描失败: ' + (error.message || '未知错误'))
  } finally {
    scanning.value = false
    scanProgress.value = 0
  }
}

function confirmDelete(device: any) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除设备 "${device.name}" 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deviceStore.removeDevice(device.id)
        message.success('删除成功')
      } catch (error) {
        message.error('删除失败')
      }
    }
  })
}

function goToDevice(id: number) {
  router.push(`/device/${id}`)
}

async function handleRefreshBattery() {
  await deviceStore.refreshBatteries()
  message.success('电量已刷新')
}

onMounted(async () => {
  // 先初始化手动 IP（如果之前设置过）
  const manualIp = localStorage.getItem('manual_local_ip')
  if (manualIp) {
    localIp.value = manualIp
  }
  // 先加载缓存电量（用于立即显示）
  deviceStore.loadCachedBatteries()
  // 然后获取设备列表
  await deviceStore.fetchDevices()
  // 最后获取最新电量数据
  await deviceStore.fetchBatteries()
  // 获取本机IP（用于扫描显示，如果没有手动设置）
  if (!localIp.value) {
    fetchLocalIp()
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h1 {
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  cursor: pointer;
  padding: 4px;
  border-radius: 50%;
  transition: background 0.2s;
}

.user-avatar:hover {
  background: #f5f7fa;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title h2 {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  margin: 0;
}

.empty-state {
  padding: 60px 0;
}

/* Device Grid */
.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.device-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  cursor: pointer;
  transition: all 0.2s ease;
}

.device-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.device-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  border-radius: 12px;
  transition: all 0.2s;
}

.device-icon.has-port {
  background: #e8f5e9;
}

.device-info {
  flex: 1;
  min-width: 0;
}

.device-info h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 6px;
}

.device-ip {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
}

.device-remark {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Scan Tab */
.scan-container {
  background: white;
  border-radius: 12px;
  padding: 24px;
}

.scan-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.scan-info h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.network-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #666;
}

.local-ip-display {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.scan-results {
  margin-top: 20px;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 10px;
  transition: all 0.2s;
}

.device-item:hover {
  background: #f0fdf4;
}

.device-item.is-known {
  background: #f5f5f5;
  border: 1px solid #e0e0e0;
}

.device-item.is-new {
  background: #f0fdf4;
  border: 1px solid #86efac;
}

.device-item-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
}

.device-item-info {
  flex: 1;
}

.device-item-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.device-item-ip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #666;
}

/* Scan Battery Display */
.scan-battery {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #f0fdf4;
  border-radius: 6px;
}

.scan-battery-icon {
  position: relative;
  width: 20px;
  height: 10px;
  border: 1.5px solid currentColor;
  border-radius: 2px;
  padding: 1px;
}

.scan-battery-icon::after {
  content: '';
  position: absolute;
  right: -4px;
  top: 50%;
  transform: translateY(-50%);
  width: 2px;
  height: 5px;
  background: currentColor;
  border-radius: 0 1px 1px 0;
}

.scan-battery-text {
  font-size: 12px;
  font-weight: 500;
  min-width: 30px;
  text-align: right;
}

.scan-actions {
  display: flex;
  gap: 12px;
}

/* Add Tab */
.add-container {
  max-width: 600px;
  margin: 0 auto;
}

.add-card {
  border-radius: 12px;
}

.add-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

/* Battery Display */
.battery-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #f8f9fa;
  border-radius: 8px;
}

.battery-icon {
  position: relative;
  width: 24px;
  height: 14px;
  border: 2px solid currentColor;
  border-radius: 3px;
  padding: 1px;
}

.battery-icon::after {
  content: '';
  position: absolute;
  right: -5px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 6px;
  background: currentColor;
  border-radius: 0 2px 2px 0;
}

.battery-text {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 500;
}

.battery-level-text {
  min-width: 36px;
  text-align: right;
}

.charging-icon {
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Battery colors */
/* Base battery level style - green by default */
.battery-level {
  background: #18a058;
  height: 100% !important;
  border-radius: 1px;
  transition: width 0.3s ease;
}

/* Scan battery icon base - uses currentColor for border */
.scan-battery-icon {
  color: #18a058;
}

/*
 * The battery-* classes (battery-high, battery-medium, etc.) are applied
 * to .scan-battery-icon via :class binding.
 * Since .battery-level is a child, we use parent.battery-* > .battery-level selector.
 */

/* Battery high - green */
.scan-battery-icon.battery-high > .battery-level {
  background: linear-gradient(90deg, #18a058, #36b368);
}

/* Battery medium - orange */
.scan-battery-icon.battery-medium > .battery-level {
  background: linear-gradient(90deg, #f0a020, #f5bf4f);
}

/* Battery low - yellow-orange */
.scan-battery-icon.battery-low > .battery-level {
  background: linear-gradient(90deg, #ff9800, #ffb74d);
}

/* Battery critical - red */
.scan-battery-icon.battery-critical > .battery-level {
  background: linear-gradient(90deg, #d03050, #e05070);
  animation: blink 1s infinite;
}

/* Battery charging - green with animation */
.scan-battery-icon.battery-charging > .battery-level {
  background: linear-gradient(90deg, #18a058, #4ade80);
  animation: charge-flow 2s infinite linear;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@keyframes charge-flow {
  0% { width: 10%; }
  50% { width: 90%; }
  100% { width: 10%; }
}
</style>
