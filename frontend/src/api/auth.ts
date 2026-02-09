import api from './index'

// Types
export interface User {
  id: number
  username: string
  avatar: string | null
  totp_enabled: boolean
  created_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface TOTPSetupResponse {
  secret: string
  qr_code: string
}

// Auth APIs
export const authApi = {
  async login(username: string, password: string, totpCode?: string): Promise<LoginResponse> {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    // totp_code 需要作为查询参数传递，不是表单字段
    const params = new URLSearchParams()
    if (totpCode !== undefined && totpCode !== '') {
      params.append('totp_code', totpCode)
    }

    const url = params.toString()
      ? `/auth/login?${params.toString()}`
      : '/auth/login'

    const response = await api.post<LoginResponse>(url, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    return response.data
  },

  async register(username: string, password: string): Promise<User> {
    const response = await api.post<User>('/auth/register', { username, password })
    return response.data
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  async getMe(): Promise<User> {
    const response = await api.get<User>('/auth/me')
    return response.data
  },

  async updateProfile(data: { username?: string; avatar?: string }): Promise<User> {
    const response = await api.put<User>('/auth/me', data)
    return response.data
  },

  async updatePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.put('/auth/password', { old_password: oldPassword, new_password: newPassword })
  },

  // TOTP
  async setup2FA(): Promise<TOTPSetupResponse> {
    const response = await api.post<TOTPSetupResponse>('/auth/2fa/setup')
    return response.data
  },

  async verify2FA(code: string): Promise<void> {
    await api.post('/auth/2fa/verify', { code })
  },

  async disable2FA(code: string): Promise<void> {
    await api.post('/auth/2fa/disable', { code })
  },

  async get2FAStatus(): Promise<{ enabled: boolean; secret_set: boolean }> {
    const response = await api.get('/auth/2fa/status')
    return response.data
  },

  async uploadAvatar(file: Blob): Promise<{ avatar_url: string }> {
    const formData = new FormData()
    formData.append('file', file, 'avatar.png')
    const response = await api.post<{ avatar_url: string }>('/auth/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  },

  async deleteAvatar(): Promise<void> {
    await api.delete('/auth/avatar')
  }
}
