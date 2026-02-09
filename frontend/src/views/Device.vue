<template>
  <div class="device-container">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <n-button quaternary circle @click="goBack">
          <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        </n-button>
        <h1>{{ deviceStore.currentDevice ? formatDeviceName(deviceStore.currentDevice.name, deviceStore.currentDevice.remark) : '设备详情' }}</h1>
      </div>
      <div class="header-right">
        <n-button :loading="testing" @click="testConnection">
          <template #icon><n-icon><WifiOutline /></n-icon></template>
          测试连接
        </n-button>
        <n-tag :type="connectionStatus">{{ connectionMessage }}</n-tag>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <n-tabs type="line" animated v-model:value="activeTab">
        <!-- SMS -->
        <n-tab-pane name="sms" tab="短信">
          <div class="panel">
            <!-- 切换按钮组 - 始终显示 -->
            <div class="panel-header">
              <n-button-group>
                <n-button :type="smsType === 1 ? 'primary' : 'default'" @click="switchSMSType(1)">
                  接收
                </n-button>
                <n-button :type="smsType !== 1 ? 'primary' : 'default'" @click="switchSMSType(2)">
                  发送
                </n-button>
              </n-button-group>

              <!-- 接收页签：显示搜索框 -->
              <template v-if="smsType === 1">
                <n-input
                  v-model:value="smsKeyword"
                  placeholder="搜索..."
                  clearable
                  style="width: 200px"
                  @keyup.enter="refreshSMS"
                />
              </template>
            </div>

            <!-- 发送页签：显示发送表单 -->
            <template v-if="smsType !== 1">
              <div class="send-sms-form">
                <div class="form-title">发送短信</div>
                <n-form label-placement="left" label-width="80" :model="smsSendForm">
                  <n-form-item label="SIM卡">
                    <n-radio-group v-model:value="smsSendForm.simSlot">
                      <n-radio :value="1">{{ deviceConfig?.sim1_number || 'SIM 1' }}</n-radio>
                      <n-radio :value="2">{{ deviceConfig?.sim2_number || 'SIM 2' }}</n-radio>
                    </n-radio-group>
                  </n-form-item>
                  <n-form-item label="手机号">
                    <n-input v-model:value="smsSendForm.phoneNumbers" placeholder="多个用分号分隔" style="flex: 1; margin-right: 12px;" />
                    <n-button type="primary" :loading="sendingSMS" @click="handleSendSMS">
                      发送
                    </n-button>
                  </n-form-item>
                  <n-form-item label="内容">
                    <n-input v-model:value="smsSendForm.content" type="textarea" :rows="3" />
                  </n-form-item>
                </n-form>
              </div>

              <div class="divider">
                <span>发送记录</span>
              </div>
            </template>

            <n-data-table
              :columns="smsColumns"
              :data="smsList"
              :loading="loadingSMS"
              striped
              :row-key="(row: SMSItem) => row.date + row.number"
            />

            <div v-if="smsList.length > 0" style="text-align: center; margin-top: 16px;">
              <n-button v-if="!loadingMoreSMS" @click="loadMoreSMS">
                加载更多
              </n-button>
              <n-spin v-else size="small" />
            </div>
            <div v-else-if="!loadingSMS" style="text-align: center; margin-top: 16px; color: #999;">
              暂无数据
            </div>
          </div>
        </n-tab-pane>

        <!-- Calls -->
        <n-tab-pane name="calls" tab="通话">
          <div class="panel">
            <div class="panel-header">
              <n-select
                v-model:value="callType"
                :options="callTypeOptions"
                style="width: 150px"
                @update:value="switchCallType"
              />
              <n-button @click="refreshCalls">
                <template #icon><n-icon><RefreshOutline /></n-icon></template>
                刷新
              </n-button>
            </div>

            <n-data-table
              :columns="callColumns"
              :data="callList"
              :loading="loadingCalls"
              striped
            />

            <div v-if="callList.length > 0" style="text-align: center; margin-top: 16px;">
              <n-button v-if="!loadingMoreCalls" @click="loadMoreCalls">
                加载更多
              </n-button>
              <n-spin v-else size="small" />
            </div>
            <div v-else-if="!loadingCalls" style="text-align: center; margin-top: 16px; color: #999;">
              暂无数据
            </div>
          </div>
        </n-tab-pane>

        <!-- Contacts -->
        <n-tab-pane name="contacts" tab="话簿">
          <div class="panel">
            <div class="panel-header">
              <n-input
                v-model:value="contactSearch"
                placeholder="搜索联系人..."
                clearable
                style="width: 250px"
                @keyup.enter="fetchContacts"
              />
              <n-button @click="showAddContact = true">
                <template #icon><n-icon><PersonAddOutline /></n-icon></template>
                添加联系人
              </n-button>
            </div>

            <n-data-table
              :columns="contactColumns"
              :data="contactList"
              :loading="loadingContacts"
              :pagination="contactPagination"
              @update:page="fetchContacts"
              striped
            />
          </div>
        </n-tab-pane>

        <!-- Other -->
        <n-tab-pane name="other" tab="其他">
          <div class="other-grid">
            <!-- 设备概览 -->
            <n-card title="设备信息" size="small" class="info-card">
              <div class="info-row">
                <span class="info-label">设备型号</span>
                <span class="info-value" style="display: flex; align-items: center; gap: 8px;">
                  {{ deviceConfig?.device_mark || '未知' }}
                  <n-button quaternary circle size="small" @click="openRemarkDialog">
                    <template #icon><n-icon><CreateOutline /></n-icon></template>
                  </n-button>
                </span>
              </div>
              <div class="info-row">
                <span class="info-label">系统版本</span>
                <span class="info-value">{{ deviceConfig?.version_name || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">SIM 1</span>
                <div class="sim-tags">
                  <n-tag size="small" type="info">{{ deviceConfig?.sim1_carrier || '-' }}</n-tag>
                  <n-tag size="small">{{ deviceConfig?.sim1_number || '' }}</n-tag>
                </div>
              </div>
              <div class="info-row">
                <span class="info-label">SIM 2</span>
                <div class="sim-tags">
                  <n-tag size="small" type="info">{{ deviceConfig?.sim2_carrier || '-' }}</n-tag>
                  <n-tag size="small">{{ deviceConfig?.sim2_number || '' }}</n-tag>
                </div>
              </div>
              <n-button v-if="!deviceConfig" @click="refreshAllStatus" :loading="loadingOther" block style="margin-top: 16px">
                获取设备信息
              </n-button>
            </n-card>

            <!-- 电池状态 -->
            <n-card title="电池状态" size="small" class="info-card">
              <div class="battery-main-row">
                <div class="battery-level-display">
                  <span class="battery-percent" :style="{ color: getBatteryColor(battery.level) }">{{ battery.level }}%</span>
                </div>
                <n-progress
                  type="line"
                  :percentage="battery.level"
                  :color="getBatteryColor(battery.level)"
                  :height="8"
                  :border-radius="4"
                  style="flex: 1; margin-left: 16px;"
                />
              </div>
              <div class="battery-meta">
                <span>{{ battery.status || '-' }}</span>
                <span>{{ battery.temperature || 0 }}°C</span>
                <span>{{ battery.plugged || '-' }}</span>
              </div>
              <n-button @click="refreshAllStatus" :loading="loadingOther" quaternary block style="margin-top: 12px">
                刷新
              </n-button>
            </n-card>

            <!-- 远程唤醒 -->
            <n-card title="远程唤醒" size="small" class="info-card">
              <n-form label-placement="top" :model="wolForm" label-width="80">
                <n-form-item label="MAC 地址" path="mac">
                  <n-input v-model:value="wolForm.mac" placeholder="AA:BB:CC:DD:EE:FF" />
                </n-form-item>
                <n-form-item label="端口" path="port">
                  <n-input-number v-model:value="wolForm.port" :min="1" :max="65535" style="width: 100%" />
                </n-form-item>
                <n-form-item>
                  <n-button type="primary" @click="sendWOL" :loading="loadingWOL" block>
                    发送唤醒包
                  </n-button>
                </n-form-item>
              </n-form>
            </n-card>
          </div>
        </n-tab-pane>
      </n-tabs>
    </main>

    <!-- Send SMS Dialog -->
    <n-modal v-model:show="showSendSMS" preset="dialog" title="发送短信" style="width: 450px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="SIM卡">
          <n-radio-group v-model:value="smsSendForm.simSlot">
            <n-radio :value="1">SIM 1</n-radio>
            <n-radio :value="2">SIM 2</n-radio>
          </n-radio-group>
        </n-form-item>
        <n-form-item label="手机号">
          <n-input v-model:value="smsSendForm.phoneNumbers" placeholder="多个用分号分隔" />
        </n-form-item>
        <n-form-item label="内容">
          <n-input v-model:value="smsSendForm.content" type="textarea" :rows="4" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showSendSMS = false">取消</n-button>
        <n-button type="primary" :loading="sendingSMS" @click="handleSendSMS">发送</n-button>
      </template>
    </n-modal>

    <!-- Add Contact Dialog -->
    <n-modal v-model:show="showAddContact" preset="dialog" title="添加联系人" style="width: 400px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="姓名">
          <n-input v-model:value="contactForm.name" placeholder="联系人姓名" />
        </n-form-item>
        <n-form-item label="电话">
          <n-input v-model:value="contactForm.phoneNumber" placeholder="手机号" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showAddContact = false">取消</n-button>
        <n-button type="primary" :loading="addingContact" @click="handleAddContact">添加</n-button>
      </template>
    </n-modal>

    <!-- Remark Dialog -->
    <n-modal v-model:show="showRemarkDialog" preset="dialog" title="编辑备注名" style="width: 350px">
      <n-form label-placement="top">
        <n-form-item label="备注名">
          <n-input v-model:value="remarkForm.nickname" placeholder="给自己看的名字" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showRemarkDialog = false">取消</n-button>
        <n-button type="primary" :loading="savingRemark" @click="saveRemark">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, NTag, NButton, NIcon, NTime } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import {
  ArrowBackOutline,
  WifiOutline,
  RefreshOutline,
  PersonAddOutline,
  CreateOutline
} from '@vicons/ionicons5'
import { useDeviceStore } from '@/stores/devices'
import { deviceApi, type SMSItem, type CallItem, type ContactItem } from '@/api/devices'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const deviceStore = useDeviceStore()

const deviceId = Number(route.params.id)
const activeTab = ref('sms')

// Format device name for display
function formatDeviceName(name: string, nickname: string | null): string {
  if (nickname) {
    return `${nickname}（${name}）`
  }
  return name
}

// Connection Status
const testing = ref(false)
const connectionStatus = ref<'success' | 'error' | 'warning'>('warning')
const connectionMessage = ref('未测试')

// Battery & Location
const battery = reactive({ level: 0, status: '-', temperature: 0, plugged: '-', scale: 100 })
const loadingOther = ref(false)

// SMS
const smsType = ref(1)
const smsKeyword = ref('')
const smsList = ref<SMSItem[]>([])
const loadingSMS = ref(false)
const loadingMoreSMS = ref(false)
const showSendSMS = ref(false)
const smsSendForm = reactive({ simSlot: 1, phoneNumbers: '', content: '' })
const sendingSMS = ref(false)
const smsPageNum = ref(1)
const smsPageSize = 20
// Check if content contains verification code
function hasVerificationCode(content: string): string | null {
  if (!content) return null

  // Chinese patterns - merge similar patterns
  const cnPatterns = [
    /(?:您的)?验证码[是为]?[：:]\s*(\d{4,8})/,  // 验证码、验证码是、验证码为、您的验证码、您的验证码是
    /[动态校验确认安全登录]码[：:]\s*(\d{4,8})/,    // 动态码、校验码、确认码、安全码、登录码
  ]

  // English patterns - merge similar patterns
  const enPatterns = [
    /verification code(?: is)?[：:\s]*(\d{4,8})/i,  // verification code、verification code is
    /your (?:\w+\s+)?code[：:\s]*(\d{4,8})/i,    // your code、your verification code
    /(?:pass|security|PIN) code[：:\s]*(\d{4,8})/i,   // pass code、security code、PIN code
  ]

  // Check Chinese patterns first
  for (const pattern of cnPatterns) {
    const match = content.match(pattern)
    if (match) return match[1]
  }

  // Then check English patterns
  for (const pattern of enPatterns) {
    const match = content.match(pattern)
    if (match) return match[1]
  }

  return null
}

// SMS content renderer with verification code detection and copy
function renderSMSContent(content: string): any {
  if (!content) return '-'

  const code = hasVerificationCode(content)
  if (code) {
    const parts = content.split(code)
    return h('span', {}, [
      parts[0] || '',
      h('u', {
        style: 'cursor: pointer; text-decoration-skip-ink: none;',
        onClick: () => copyToClipboard(code)
      }, code),
      parts[1] || ''
    ])
  }
  return content
}

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch {
    // Fallback for older browsers
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    message.success('已复制到剪贴板')
  }
}

// SMS cache: key = "type_keyword", value = message array
const smsCache = new Map<string, { list: SMSItem[], page: number }>()

// Helper to display name or "未知"
function displayName(name: string | null): string {
  if (!name || name === '未知号码') return '未知'
  return name
}

const smsColumns: DataTableColumns<SMSItem> = [
  { title: '姓名', key: 'name', width: 70, render: row => h('span', { style: 'white-space: nowrap;' }, displayName(row.name)) },
  { title: '号码', key: 'number', width: 150, render: row => h('span', { style: 'white-space: nowrap; color: #666; font-family: monospace;' }, row.number) },
  { title: '时间', key: 'date', width: 130, render: row => h('span', { style: 'white-space: nowrap;' }, new Date(Number(row.date)).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit' }).replace(/\./g, '-').replace(/,/g, '')) },
  { title: '内容', key: 'content', ellipsis: { tooltip: true }, render: row => renderSMSContent(row.content) }
]

// Calls
const callType = ref(0)
const callList = ref<CallItem[]>([])
const loadingCalls = ref(false)
const loadingMoreCalls = ref(false)
const callPageNum = ref(1)
const callPageSize = 20
// Call cache: key = "type", value = call array
const callCache = new Map<number, { list: CallItem[], page: number }>()
const callTypeOptions = [
  { label: '全部', value: 0 },
  { label: '呼入', value: 1 },
  { label: '呼出', value: 2 },
  { label: '未接', value: 3 }
]

const callColumns: DataTableColumns<CallItem> = [
  { title: '姓名', key: 'name', render: row => row.name || '未知' },
  { title: '号码', key: 'number' },
  { title: '时长', key: 'duration', render: row => `${row.duration}s` },
  { title: '时间', key: 'date_long', render: row => h(NTime, { to: new Date(row.date_long) }, { default: () => new Date(row.date_long).toLocaleString() }) },
  { title: '类型', key: 'type', render: row => {
    const callTypeMap = ['呼入', '呼出', '未接']
    const callTypeColors: ('info' | 'success' | 'warning')[] = ['info', 'success', 'warning']
    const typeIndex = Math.min(row.type, 2)
    return h(NTag, { size: 'small', type: callTypeColors[typeIndex] || 'default' }, { default: () => callTypeMap[typeIndex] || '未知' })
  }}
]

// Contacts
const contactSearch = ref('')
const contactList = ref<ContactItem[]>([])
const loadingContacts = ref(false)
const showAddContact = ref(false)
const contactForm = reactive({ name: '', phoneNumber: '' })
const addingContact = ref(false)
const contactPagination = reactive({ page: 1, pageSize: 20, itemCount: 0 })

// Remark
const showRemarkDialog = ref(false)
const remarkForm = reactive({ nickname: '' })
const savingRemark = ref(false)

const contactColumns: DataTableColumns<ContactItem> = [
  { title: '姓名', key: 'name' },
  { title: '电话', key: 'phone_number' }
]

// WOL
const wolForm = reactive({ mac: '', ip: '', port: 9 })
const loadingWOL = ref(false)

// Config
const deviceConfig = ref<any>(null)

function goBack() {
  router.push('/')
}

async function testConnection() {
  testing.value = true
  try {
    const result = await deviceStore.testDevice(deviceId)
    connectionStatus.value = result.success ? 'success' : 'error'
    connectionMessage.value = result.message
    if (result.success) {
      message.success('连接成功')
    } else {
      message.error(result.message)
    }
  } catch (error) {
    connectionStatus.value = 'error'
    connectionMessage.value = '连接失败'
  } finally {
    testing.value = false
  }
}

// Get battery color based on level
function getBatteryColor(level: number): string {
  if (level >= 80) return '#18a058'
  if (level >= 50) return '#f0a020'
  return '#d03050'
}

// Refresh all status data
async function refreshAllStatus() {
  loadingOther.value = true
  try {
    await Promise.all([
      deviceApi.getConfig(deviceId).then(data => { deviceConfig.value = data }),
      deviceApi.queryBattery(deviceId).then(data => { Object.assign(battery, data) })
    ])
  } catch (error) {
    message.error('获取设备状态失败')
  } finally {
    loadingOther.value = false
  }
}

// Get cache key for SMS
function getSMSCacheKey(): string {
  return `${smsType.value}_${smsKeyword.value || ''}`
}

// Fetch SMS with cache support
async function fetchSMS(forceRefresh = false) {
  const cacheKey = getSMSCacheKey()
  const cached = smsCache.get(cacheKey)

  // If has cache and not force refresh, use cache
  if (!forceRefresh && cached) {
    smsList.value = cached.list
    smsPageNum.value = cached.page
    return
  }

  loadingSMS.value = true
  try {
    const data = await deviceApi.querySMS(deviceId, smsType.value, 1, smsPageSize, smsKeyword.value || undefined)
    smsList.value = data.messages
    smsPageNum.value = 1
    // Save to cache
    smsCache.set(cacheKey, { list: data.messages, page: 1 })
  } catch (error) {
    message.error('获取短信失败')
  } finally {
    loadingSMS.value = false
  }
}

// Refresh SMS - clear cache and reload
function refreshSMS() {
  smsCache.delete(getSMSCacheKey())
  smsKeyword.value = ''
  fetchSMS(true)
}

// Load more SMS - append to existing list
async function loadMoreSMS() {
  const cacheKey = getSMSCacheKey()
  const cached = smsCache.get(cacheKey)
  if (!cached) return

  loadingMoreSMS.value = true
  try {
    const nextPage = cached.page + 1
    const data = await deviceApi.querySMS(deviceId, smsType.value, nextPage, smsPageSize, smsKeyword.value || undefined)

    if (data.messages.length > 0) {
      smsList.value = [...smsList.value, ...data.messages]
      smsPageNum.value = nextPage
      // Update cache
      smsCache.set(cacheKey, { list: smsList.value, page: nextPage })
    } else {
      message.info('没有更多数据了')
    }
  } catch (error) {
    message.error('加载更多失败')
  } finally {
    loadingMoreSMS.value = false
  }
}

// Switch SMS type - use cache if available
function switchSMSType(type: number) {
  if (smsType.value === type) return
  smsType.value = type
}

async function handleSendSMS() {
  if (!smsSendForm.phoneNumbers || !smsSendForm.content) {
    message.warning('请填写完整信息')
    return
  }
  sendingSMS.value = true
  try {
    await deviceApi.sendSMS(deviceId, smsSendForm.simSlot, smsSendForm.phoneNumbers, smsSendForm.content)
    message.success('发送成功')
    // 清空表单
    smsSendForm.phoneNumbers = ''
    smsSendForm.content = ''
    // 清除发送短信的缓存并刷新列表
    smsCache.delete('2_')
    // 切换到发送短信 tab 并刷新列表
    smsType.value = 2
    fetchSMS()
  } catch (error) {
    message.error('发送失败')
  } finally {
    sendingSMS.value = false
  }
}

// Fetch calls with cache support
async function fetchCalls(forceRefresh = false) {
  const cached = callCache.get(callType.value)

  // If has cache and not force refresh, use cache
  if (!forceRefresh && cached) {
    callList.value = cached.list
    callPageNum.value = cached.page
    return
  }

  loadingCalls.value = true
  try {
    const data = await deviceApi.queryCalls(deviceId, callType.value, 1, callPageSize)
    callList.value = data.calls
    callPageNum.value = 1
    // Save to cache
    callCache.set(callType.value, { list: data.calls, page: 1 })
  } catch (error) {
    message.error('获取通话记录失败')
  } finally {
    loadingCalls.value = false
  }
}

// Refresh calls - clear cache and reload
function refreshCalls() {
  callCache.delete(callType.value)
  fetchCalls(true)
}

// Load more calls - append to existing list
async function loadMoreCalls() {
  const cached = callCache.get(callType.value)
  if (!cached) return

  loadingMoreCalls.value = true
  try {
    const nextPage = cached.page + 1
    const data = await deviceApi.queryCalls(deviceId, callType.value, nextPage, callPageSize)

    if (data.calls.length > 0) {
      callList.value = [...callList.value, ...data.calls]
      callPageNum.value = nextPage
      // Update cache
      callCache.set(callType.value, { list: callList.value, page: nextPage })
    } else {
      message.info('没有更多数据了')
    }
  } catch (error) {
    message.error('加载更多失败')
  } finally {
    loadingMoreCalls.value = false
  }
}

// Switch call type - use cache if available
function switchCallType() {
  const cached = callCache.get(callType.value)
  if (cached) {
    callList.value = cached.list
    callPageNum.value = cached.page
  } else {
    fetchCalls()
  }
}

async function fetchContacts() {
  loadingContacts.value = true
  try {
    const data = await deviceApi.queryContacts(deviceId, contactSearch.value || undefined)
    contactList.value = data.contacts
    contactPagination.itemCount = data.contacts.length
  } catch (error) {
    message.error('获取联系人失败')
  } finally {
    loadingContacts.value = false
  }
}

async function handleAddContact() {
  if (!contactForm.phoneNumber) {
    message.warning('请输入手机号')
    return
  }
  addingContact.value = true
  try {
    await deviceApi.addContact(deviceId, contactForm.phoneNumber, contactForm.name)
    message.success('添加成功')
    showAddContact.value = false
    contactForm.name = ''
    contactForm.phoneNumber = ''
    fetchContacts()
  } catch (error) {
    message.error('添加失败')
  } finally {
    addingContact.value = false
  }
}

// Open remark dialog
function openRemarkDialog() {
  remarkForm.nickname = deviceStore.currentDevice?.remark || ''
  showRemarkDialog.value = true
}

// Save remark
async function saveRemark() {
  savingRemark.value = true
  try {
    await deviceApi.update(deviceId, {
      remark: remarkForm.nickname || undefined
    })
    message.success('备注保存成功')
    showRemarkDialog.value = false
    // Refresh device data
    await deviceStore.fetchDevice(deviceId)
  } catch (error) {
    message.error('保存失败')
  } finally {
    savingRemark.value = false
  }
}

async function sendWOL() {
  if (!wolForm.mac) {
    message.warning('请输入MAC地址')
    return
  }
  loadingWOL.value = true
  try {
    await deviceApi.sendWOL(deviceId, wolForm.mac, wolForm.ip || undefined, wolForm.port)
    message.success('唤醒包已发送')
  } catch (error) {
    message.error('发送失败')
  } finally {
    loadingWOL.value = false
  }
}

onMounted(async () => {
  await deviceStore.fetchDevice(deviceId)
  testConnection()
  refreshAllStatus()
  fetchSMS()
})

// Tab change handler - fetch data when switching tabs
watch(activeTab, (newTab) => {
  if (newTab === 'sms') {
    fetchSMS()
  } else if (newTab === 'calls') {
    fetchCalls()
  } else if (newTab === 'contacts') {
    fetchContacts()
  }
})

// SMS type change handler - use cache if available, otherwise fetch
watch(smsType, () => {
  const cacheKey = getSMSCacheKey()
  const cached = smsCache.get(cacheKey)
  if (cached) {
    smsList.value = cached.list
    smsPageNum.value = cached.page
  } else {
    fetchSMS()
  }
})
</script>

<style scoped>
.device-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h1 {
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.other-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.info-card {
  background: white;
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease;
}

.info-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f5;
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 13px;
  color: #999;
}

.info-value {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.sim-tags {
  display: flex;
  gap: 6px;
}

.battery-main-row {
  display: flex;
  align-items: center;
  margin: 16px 0;
}

.battery-percent {
  font-size: 32px;
  font-weight: 600;
  min-width: 70px;
}

.battery-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  padding: 8px 0;
}

.status-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.device-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.device-name {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.status-section {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #999;
}

.info-value {
  font-size: 14px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

.battery-section {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 16px;
}

.battery-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.battery-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.battery-level {
  font-size: 20px;
  font-weight: 600;
}

.battery-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 13px;
  color: #666;
}

.battery-detail {
  font-size: 12px;
  color: #999;
}

.status-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #999;
}

.status-loading p {
  margin-top: 16px;
}

.panel {
  background: white;
  border-radius: 12px;
  padding: 20px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.api-flags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.panel-header:only-child {
  justify-content: flex-end;
}

.send-sms-form {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.form-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #333;
}

.divider {
  display: flex;
  align-items: center;
  margin: 20px 0;
  color: #999;
  font-size: 13px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e8e8e8;
}

.divider span {
  padding: 0 16px;
}

.sms-content-full {
  white-space: pre-wrap;
  word-break: break-all;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  margin-top: 8px;
  max-height: 200px;
  overflow-y: auto;
}

@media (max-width: 600px) {
  .status-section {
    grid-template-columns: 1fr;
  }
}
</style>
