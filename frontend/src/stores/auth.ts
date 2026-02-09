import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/api/auth'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token'))
  const loading = ref(false)

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '')

  // Avatar with cache buster - updated explicitly when avatar changes
  let avatarCacheBuster = 0

  const avatar = computed(() => {
    if (!user.value?.avatar) return null
    const baseUrl = user.value.avatar.startsWith('/') ? user.value.avatar : '/' + user.value.avatar
    return baseUrl + '?cb=' + avatarCacheBuster
  })

  const totpEnabled = computed(() => user.value?.totp_enabled || false)

  function refreshAvatar() {
    avatarCacheBuster++
  }

  async function login(username: string, password: string, totpCode?: string) {
    loading.value = true
    try {
      const response = await authApi.login(username, password, totpCode)
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      await fetchUser()
      return true
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      token.value = null
      user.value = null
      localStorage.removeItem('token')
    }
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      user.value = await authApi.getMe()
      refreshAvatar()
    } catch {
      token.value = null
      localStorage.removeItem('token')
    }
  }

  async function updateProfile(data: { username?: string; avatar?: string }) {
    user.value = await authApi.updateProfile(data)
  }

  async function register(username: string, password: string) {
    await authApi.register(username, password)
  }

  async function updatePassword(oldPassword: string, newPassword: string) {
    await authApi.updatePassword(oldPassword, newPassword)
  }

  async function setup2FA() {
    return await authApi.setup2FA()
  }

  async function verify2FA(code: string) {
    await authApi.verify2FA(code)
    await fetchUser()
  }

  async function disable2FA(code: string) {
    await authApi.disable2FA(code)
    await fetchUser()
  }

  async function uploadAvatar(file: Blob): Promise<void> {
    await authApi.uploadAvatar(file)
    // Refresh avatar after upload
    await fetchUser()
  }

  // Initialize
  if (token.value) {
    fetchUser()
  }

  return {
    user,
    token,
    loading,
    isLoggedIn,
    username,
    avatar,
    totpEnabled,
    login,
    logout,
    fetchUser,
    updateProfile,
    register,
    updatePassword,
    setup2FA,
    verify2FA,
    disable2FA,
    uploadAvatar,
    refreshAvatar
  }
})
