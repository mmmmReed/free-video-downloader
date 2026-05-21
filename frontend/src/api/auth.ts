import { http } from './http'

export interface AuthMe {
  id: number
  email: string
  vip_until: number | null
  is_vip: boolean
}

export async function register(email: string, password: string): Promise<string> {
  const { data } = await http.post<{ access_token: string }>('/auth/register', {
    email,
    password,
  })
  return data.access_token
}

export async function login(email: string, password: string): Promise<string> {
  const { data } = await http.post<{ access_token: string }>('/auth/login', {
    email,
    password,
  })
  return data.access_token
}

export async function fetchMe(): Promise<AuthMe> {
  const { data } = await http.get<AuthMe>('/auth/me')
  return data
}
