import { http } from './http'

export async function createCheckoutSession(): Promise<string> {
  const { data } = await http.post<{ url: string }>('/billing/checkout-session', {})
  return data.url
}

export async function verifyCheckoutSession(sessionId: string): Promise<{
  ok: boolean
  vip_until: number | null
  is_vip: boolean
}> {
  const { data } = await http.post<{
    ok: boolean
    vip_until: number | null
    is_vip: boolean
  }>('/billing/verify-session', { session_id: sessionId })
  return data
}
