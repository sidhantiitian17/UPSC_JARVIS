import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, getHealth } from './client'

function bridge(res: { status: number; body: unknown }): ReturnType<typeof vi.fn> {
  const call = vi.fn(async () => res)
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api: call,
    status: async () => ({ ready: true })
  }
  return call
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('renderer api client', () => {
  it('sends requests through the preload bridge and returns the body', async () => {
    const call = bridge({ status: 200, body: { status: 'ok', version: '0.1.0' } })
    expect(await getHealth()).toEqual({ status: 'ok', version: '0.1.0' })
    expect(call).toHaveBeenCalledWith({ method: 'GET', path: '/health', body: undefined })
  })

  it('throws ApiError with status and body on non-2xx', async () => {
    bridge({ status: 401, body: { detail: 'nope' } })
    const err = await api('GET', '/health').catch((e) => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err).toMatchObject({ status: 401, body: { detail: 'nope' } })
  })
})
