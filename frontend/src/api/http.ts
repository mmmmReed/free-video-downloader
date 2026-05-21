import axios from 'axios'
import { getApiBase } from './base'

export const http = axios.create({
  timeout: 120000,
})

http.interceptors.request.use((config) => {
  config.baseURL = getApiBase()
  const t = localStorage.getItem('auth_token')
  if (t) {
    config.headers.Authorization = `Bearer ${t}`
  }
  return config
})
