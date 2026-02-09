<template>
  <div class="profile-container">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <n-button quaternary circle @click="goBack">
          <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
        </n-button>
        <h1>个人中心</h1>
      </div>
    </header>

    <div class="profile-layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="user-card">
          <div class="avatar-wrapper" @click="showAvatarDialog = true">
            <n-avatar
              v-if="authStore.avatar"
              :src="authStore.avatar"
              :size="100"
              round
              class="user-avatar"
            />
            <n-avatar v-else round :size="100" style="background-color: #18a058" class="user-avatar">
              {{ authStore.username.charAt(0).toUpperCase() }}
            </n-avatar>
            <div class="avatar-overlay">
              <n-icon size="24"><CameraOutline /></n-icon>
              <span>更换头像</span>
            </div>
          </div>
          <h3>{{ authStore.username }}</h3>
          <n-tag v-if="authStore.totpEnabled" type="success" size="small">
            2FA 已启用
          </n-tag>
          <n-tag v-else type="warning" size="small">
            2FA 未启用
          </n-tag>
        </div>

        <n-menu
          v-model:value="activeMenu"
          :options="menuOptions"
          @update:value="handleMenuSelect"
        />
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <!-- Profile Tab -->
        <n-card v-if="activeMenu === 'profile'" title="基本信息">
          <n-form label-placement="left" label-width="100">
            <n-form-item label="用户名">
              <n-input v-model:value="profileForm.username" placeholder="用户名" />
            </n-form-item>
            <n-form-item>
              <n-button type="primary" @click="updateProfile" :loading="saving">
                保存修改
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>

        <!-- Password Tab -->
        <n-card v-if="activeMenu === 'password'" title="修改密码">
          <n-form label-placement="left" label-width="120">
            <n-form-item label="当前密码">
              <n-input
                v-model:value="passwordForm.oldPassword"
                type="password"
                show-password-on="click"
              />
            </n-form-item>
            <n-form-item label="新密码">
              <n-input
                v-model:value="passwordForm.newPassword"
                type="password"
                show-password-on="click"
              />
            </n-form-item>
            <n-form-item label="确认新密码">
              <n-input
                v-model:value="passwordForm.confirmPassword"
                type="password"
                show-password-on="click"
              />
            </n-form-item>
            <n-form-item>
              <n-button type="primary" @click="updatePassword" :loading="saving">
                修改密码
              </n-button>
            </n-form-item>
          </n-form>
        </n-card>

        <!-- 2FA Tab -->
        <n-card v-if="activeMenu === '2fa'" title="两步验证">
          <div v-if="!authStore.totpEnabled" class="twofa-setup">
            <!-- 二维码 -->
            <div v-if="totpSetup?.qr_code" class="qr-code">
              <img :src="totpSetup.qr_code" alt="TOTP QR Code" />
            </div>

            <!-- 密钥 -->
            <p v-if="totpSetup?.secret" class="secret-display">
              <span class="label">密钥：</span>
              <code>{{ totpSetup.secret }}</code>
            </p>

            <!-- 验证码输入框 -->
            <n-input
              v-if="totpSetup"
              v-model:value="totpCode"
              placeholder="请输入验证码"
              maxlength="6"
              size="large"
              class="totp-input"
              @keyup.enter="verify2FA"
            />

            <!-- 启用按钮 -->
            <n-button
              v-if="totpSetup"
              type="primary"
              size="large"
              class="verify-btn"
              @click="verify2FA"
              :loading="verifying"
              :disabled="totpCode.length !== 6"
            >
              启用
            </n-button>

            <!-- 加载状态 -->
            <div v-else class="loading-state">
              <n-spin size="large" />
            </div>
          </div>

          <div v-else class="twofa-disable">
            <n-result
              status="success"
              title="两步验证已启用"
              description="您的账户已受到双重保护。"
            />
            <n-button type="warning" @click="showDisableDialog = true">
              禁用两步验证
            </n-button>
          </div>
        </n-card>
      </main>
    </div>

    <!-- Avatar Upload Dialog -->
    <n-modal v-model:show="showAvatarDialog" preset="card" title="更换头像" style="width: 400px">
      <div class="avatar-upload-container">
        <!-- Cropper -->
        <div v-if="avatarImage" class="cropper-wrapper">
          <cropper
            ref="cropperRef"
            :src="avatarImage"
            :style="cropperStyle"
            :auto-crop-area="1"
            :view-mode="1"
            :aspect-ratio="1"
            background="transparent"
          />
        </div>

        <!-- Upload Area -->
        <div v-else class="upload-area" @click="triggerUpload">
          <input
            ref="fileInputRef"
            type="file"
            accept="image/*"
            @change="handleFileSelect"
            style="display: none"
          />
          <n-empty description="点击上传图片">
            <template #icon>
              <n-icon size="48" color="#ccc"><CloudUploadOutline /></n-icon>
            </template>
          </n-empty>
        </div>

        <!-- Preview -->
        <div v-if="previewUrl" class="preview-section">
          <p>预览：</p>
          <div class="preview-avatar">
            <n-avatar :src="previewUrl" :size="80" round />
          </div>
        </div>
      </div>

      <template #footer>
        <div class="avatar-actions">
          <n-button @click="cancelAvatarChange">取消</n-button>
          <n-button
            type="primary"
            :loading="uploading"
            :disabled="!avatarImage || !cropperRef"
            @click="uploadAvatar"
          >
            保存头像
          </n-button>
        </div>
      </template>
    </n-modal>

    <!-- Disable 2FA Dialog -->
    <n-modal v-model:show="showDisableDialog" preset="dialog" title="禁用两步验证">
      <n-form label-placement="left" label-width="120">
        <n-form-item label="验证码">
          <n-input
            v-model:value="disableCode"
            placeholder="请输入当前验证码"
            maxlength="6"
          />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showDisableDialog = false">取消</n-button>
        <n-button type="warning" @click="disable2FA" :loading="disabling">
          禁用
        </n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NIcon } from 'naive-ui'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import {
  ArrowBackOutline,
  PersonOutline,
  LockClosedOutline,
  ShieldCheckmarkOutline,
  CameraOutline,
  CloudUploadOutline
} from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const activeMenu = ref('profile')

// Menu options
const menuOptions = [
  {
    label: '基本信息',
    key: 'profile',
    icon: () => h(NIcon, null, { default: () => h(PersonOutline) })
  },
  {
    label: '修改密码',
    key: 'password',
    icon: () => h(NIcon, null, { default: () => h(LockClosedOutline) })
  },
  {
    label: '两步验证',
    key: '2fa',
    icon: () => h(NIcon, null, { default: () => h(ShieldCheckmarkOutline) })
  }
]

function handleMenuSelect(key: string) {
  activeMenu.value = key
}

function goBack() {
  router.back()
}

// Profile
const saving = ref(false)
const profileForm = reactive({
  username: ''
})

async function updateProfile() {
  saving.value = true
  try {
    await authStore.updateProfile({
      username: profileForm.username || undefined
    })
    message.success('保存成功')
  } catch (error: any) {
    message.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// Password
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

async function updatePassword() {
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    message.error('两次输入的密码不一致')
    return
  }
  if (passwordForm.newPassword.length < 6) {
    message.error('新密码至少需要6个字符')
    return
  }
  saving.value = true
  try {
    await authStore.updatePassword(passwordForm.oldPassword, passwordForm.newPassword)
    message.success('密码已修改')
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (error: any) {
    console.error('修改密码失败:', error)
    const detail = error.response?.data?.detail
    if (detail) {
      message.error(detail)
    } else {
      message.error('修改失败')
    }
  } finally {
    saving.value = false
  }
}

// 2FA
const totpSetup = ref<{ secret: string; qr_code: string } | null>(null)
const totpCode = ref('')
const initing = ref(false)
const verifying = ref(false)
const showDisableDialog = ref(false)
const disableCode = ref('')
const disabling = ref(false)

// 监听菜单切换，进入2FA菜单时初始化
watch(activeMenu, async (newVal, oldVal) => {
  // 只在进入2FA菜单时初始化
  if (newVal === '2fa' && oldVal !== '2fa') {
    // 只有在totp未启用且没有setup信息时才初始化
    if (!authStore.totpEnabled && !totpSetup.value) {
      await init2FASetup()
    }
  }
  // 离开菜单时重置状态
  if (oldVal === '2fa' && newVal !== '2fa') {
    totpSetup.value = null
    totpCode.value = ''
  }
})

async function init2FASetup() {
  initing.value = true
  try {
    totpSetup.value = await authStore.setup2FA()
  } catch (error: any) {
    message.error(error.response?.data?.detail || '获取二维码失败')
    // 重置状态防止页面一直转圈
    totpSetup.value = null
  } finally {
    initing.value = false
  }
}

async function verify2FA() {
  if (totpCode.value.length !== 6) {
    message.error('请输入6位验证码')
    return
  }
  verifying.value = true
  try {
    await authStore.verify2FA(totpCode.value)
    message.success('两步验证已启用')
    totpSetup.value = null
    totpCode.value = ''
  } catch (error: any) {
    message.error(error.response?.data?.detail || '验证失败')
  } finally {
    verifying.value = false
  }
}

async function disable2FA() {
  if (disableCode.value.length !== 6) {
    message.error('请输入6位验证码')
    return
  }
  disabling.value = true
  try {
    await authStore.disable2FA(disableCode.value)
    message.success('两步验证已禁用')
    showDisableDialog.value = false
    disableCode.value = ''
    totpCode.value = ''
    // 禁用成功后直接获取新的setup信息，避免再调用init2FASetup()
    const newSetup = await authStore.setup2FA()
    totpSetup.value = newSetup
  } catch (error: any) {
    message.error(error.response?.data?.detail || '禁用失败')
    // 出错时重置状态
    totpSetup.value = null
  } finally {
    disabling.value = false
  }
}

// Avatar Upload
const showAvatarDialog = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const cropperRef = ref<any>(null)
const avatarImage = ref<string | null>(null)
const previewUrl = ref<string | null>(null)
const uploading = ref(false)

const cropperStyle = {
  maxWidth: '100%',
  maxHeight: '300px'
}

function triggerUpload() {
  fileInputRef.value?.click()
}

function handleFileSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  // Validate file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    message.error('仅支持 JPEG、PNG、GIF 和 WebP 格式的图片')
    return
  }

  // Validate file size (max 10MB)
  if (file.size > 10 * 1024 * 1024) {
    message.error('图片大小不能超过 10MB')
    return
  }

  // Read file as data URL
  const reader = new FileReader()
  reader.onload = (e) => {
    avatarImage.value = e.target?.result as string
  }
  reader.readAsDataURL(file)

  // Clear file input
  ;(event.target as HTMLInputElement).value = ''
}

function cancelAvatarChange() {
  showAvatarDialog.value = false
  avatarImage.value = null
  previewUrl.value = null
}

async function uploadAvatar() {
  if (!cropperRef.value) return

  uploading.value = true
  try {
    // Get cropped canvas from cropper ref
    const result = cropperRef.value.getResult()
    if (!result || !result.canvas) {
      throw new Error('Failed to get crop result')
    }
    const canvas = result.canvas

    // Convert to blob
    const blob = await new Promise<Blob | null>((resolve) => {
      canvas.toBlob((b: Blob | null) => {
        resolve(b)
      }, 'image/png', 0.9)
    })

    if (!blob) {
      throw new Error('Failed to create image blob')
    }

    // Create form data
    const formData = new FormData()
    formData.append('file', blob, 'avatar.png')

    // Upload to server using store (will update avatar immediately)
    await authStore.uploadAvatar(blob)

    message.success('头像已更新')
    cancelAvatarChange()
  } catch (error: any) {
    message.error(error.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  if (authStore.user) {
    profileForm.username = authStore.user.username
  }
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background: #f5f7fa;
}

.header {
  display: flex;
  align-items: center;
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

.profile-layout {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  gap: 24px;
}

.sidebar {
  width: 260px;
  flex-shrink: 0;
}

.user-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  margin-bottom: 16px;
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
  transition: all 0.3s ease;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

.avatar-wrapper:hover .user-avatar {
  transform: scale(1.05);
}

.user-avatar {
  transition: transform 0.3s ease;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  color: white;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.user-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.main-content {
  flex: 1;
  min-width: 0;
}

/* Avatar Upload Styles */
.avatar-upload-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cropper-wrapper {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.upload-area {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  background: #fafafa;
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: #18a058;
  background: #f5fdf6;
}

.preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.preview-section p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.preview-avatar {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 50%;
}

.avatar-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.twofa-setup {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 24px;
}

.totp-input {
  width: 200px;
  text-align: center;
  font-size: 20px;
  letter-spacing: 4px;
}

.totp-input :deep(.n-input__input-el) {
  text-align: center;
  letter-spacing: 4px;
}

.verify-btn {
  width: 200px;
  height: 44px;
}

.loading-state {
  padding: 48px;
}

.qr-code {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.qr-code img {
  width: 160px;
  height: 160px;
  display: block;
}

.secret-display {
  margin: 0;
  font-size: 14px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}

.secret-display .label {
  color: #999;
}

.secret-display code {
  background: #f5f7fa;
  padding: 4px 12px;
  border-radius: 6px;
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 13px;
  letter-spacing: 1px;
  color: #333;
}

.twofa-disable {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 24px;
}

@media (max-width: 768px) {
  .profile-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
  }
}
</style>
