<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo">
        <n-icon size="48" color="#18a058">
          <PhonePortraitOutline />
        </n-icon>
        <h1>SmsManager</h1>
      </div>

      <n-form ref="loginFormRef" :model="loginForm" :rules="loginRules">
        <n-form-item path="username" label="用户名">
          <n-input v-model:value="loginForm.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item path="password" label="密码">
          <n-input
            v-model:value="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password-on="click"
            @keyup.enter="handleLogin"
          />
        </n-form-item>
        <n-form-item v-if="showTOTP" path="totpCode" label="两步验证码">
          <n-input
            v-model:value="loginForm.totpCode"
            placeholder="请输入6位验证码（如未启用2FA可留空）"
            maxlength="6"
          />
        </n-form-item>
        <n-button
          type="primary"
          block
          :loading="authStore.loading"
          @click="handleLogin"
        >
          登录
        </n-button>
      </n-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { PhonePortraitOutline } from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const message = useMessage()
const authStore = useAuthStore()

const loginFormRef = ref()
// 默认显示验证码输入框（支持 2FA）
const showTOTP = ref(true)

const loginForm = reactive({
  username: 'admin',
  password: 'admin',
  totpCode: ''
})

const loginRules = {
  username: { required: true, message: '请输入用户名' },
  password: { required: true, message: '请输入密码' }
}

async function handleLogin() {
  try {
    await loginFormRef.value?.validate()
    await authStore.login(loginForm.username, loginForm.password, loginForm.totpCode || undefined)
    message.success('登录成功')
    router.push('/')
  } catch (error: any) {
    // 如果是验证错误（不是 API 错误），说明是验证码问题
    if (!error.response) {
      message.warning('验证码为6位')
    } else if (error.response?.data?.detail?.includes('验证码')) {
      message.error(error.response?.data?.detail || '验证码错误')
    } else {
      message.error(error.response?.data?.detail || '登录失败')
    }
  }
}

// Auto-login with default credentials if available
onMounted(() => {
  if (loginForm.username && loginForm.password) {
    // Optional: Auto-login, uncomment below to enable
    // handleLogin()
  }
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.logo {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.logo h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

:deep(.n-form-item) {
  margin-bottom: 20px;
}

:deep(.n-button) {
  margin-top: 8px;
}
</style>
