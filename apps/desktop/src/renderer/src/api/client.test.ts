import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, getHealth, startupRetry } from './client'

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

  it('waits for a booting sidecar (503 sidecar-not-ready) and then succeeds', async () => {
    Object.assign(startupRetry, { tries: 5, delayMs: 1 })
    const call = vi
      .fn()
      .mockResolvedValueOnce({ status: 503, body: { error: 'sidecar-not-ready' } })
      .mockResolvedValueOnce({ status: 503, body: { error: 'sidecar-not-ready' } })
      .mockResolvedValueOnce({ status: 200, body: { status: 'ok', version: '0.1.0' } })
    ;(window as unknown as { jarvis: unknown }).jarvis = {
      platform: 'test',
      api: call,
      status: async () => ({ ready: true })
    }
    expect(await getHealth()).toEqual({ status: 'ok', version: '0.1.0' })
    expect(call).toHaveBeenCalledTimes(3)
  })

  it('gives up after the retry budget and does not retry other 503s', async () => {
    Object.assign(startupRetry, { tries: 2, delayMs: 1 })
    const call = bridge({ status: 503, body: { error: 'sidecar-not-ready' } })
    await expect(api('GET', '/health')).rejects.toMatchObject({ status: 503 })
    expect(call).toHaveBeenCalledTimes(3)
    const other = bridge({ status: 503, body: { error: 'something-else' } })
    await expect(api('GET', '/health')).rejects.toMatchObject({ status: 503 })
    expect(other).toHaveBeenCalledTimes(1)
  })
})
