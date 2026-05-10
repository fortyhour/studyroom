import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => {
    if (!user.value) return false
    const roles = user.value.roles || []
    return roles.some(r => {
      const name = typeof r === 'string' ? r : r.role_name
      return name === '管理员' || name === '超级管理员'
    })
  })

  async function login(username, password) {
    const res = await authAPI.login({ username, password })
    token.value = res.data.access_token
    user.value = res.data.user
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    return res.data.user
  }

  async function register(username, password, email) {
    await authAPI.register({ username, password, email })
  }

  async function fetchUser() {
    const res = await authAPI.me()
    user.value = res.data
    localStorage.setItem('user', JSON.stringify(res.data))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, isAdmin, login, register, fetchUser, logout }
})