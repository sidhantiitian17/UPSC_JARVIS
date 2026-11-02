// @vitest-environment node
import { describe, expect, it, vi } from 'vitest'
import { createApiProxy } from './api-proxy'

const TOKEN = 'a'.repeat(32)
const BASE = 'http://127.0.0.1:5555'

function okFetch(body: unknown = { status: 'ok' }, status = 200): typeof fetch {
  return vi.fn(
    async () => new Response(JSON.stringify(body), { status })
  ) as unknown as typeof fetch
}

describe('api proxy (token never leaves the main process)', () => {
  it('adds the bearer token and returns status and parsed body', async () => {
    const f = okFetch({ hello: 1 })
    const proxy = createApiProxy({ baseUrl: BASE, token: TOKEN, fetchImpl: f })
    const res = await proxy({ method: 'GET', path: '/health' })
    expect(res).toEqual({ status: 200, body: { hello: 1 } })
    const [url, init] = (f as unknown as ReturnType<typeof vi.fn>).mock.calls[0]
    expect(url).toBe(`${BASE}/health`)
    expect((init as RequestInit).headers).toMatchObject({ Authorization: `Bearer ${TOKEN}` })
  })

  it('sends JSON bodies for POST', async () => {
    const f = okFetch({}, 201)
    const proxy = createApiProxy({ baseUrl: BASE, token: TOKEN, fetchImpl: f })
    await proxy({ method: 'POST', path: '/x', body: { a: 1 } })
    const init = (f as unknown as ReturnType<typeof vi.fn>).mock.calls[0][1] as RequestInit
    expect(init.body).toBe('{"a":1}')
    expect(init.method).toBe('POST')
  })

  it.each([
    'http://evil.example/x',
    '//evil.example',
    '/../etc/passwd',
    '\\\\evil',
    'health',
    '/a#b',
    '/a b',
    ''
  ])('rejects unsafe path %j', async (path) => {
    const f = okFetch()
    const proxy = createApiProxy({ baseUrl: BASE, token: TOKEN, fetchImpl: f })
    await expect(proxy({ method: 'GET', path })).rejects.toThrow(/invalid api request/)
    expect(f).not.toHaveBeenCalled()
  })

  it('rejects methods outside the whitelist', async () => {
    const proxy = createApiProxy({ baseUrl: BASE, token: TOKEN, fetchImpl: okFetch() })
    await expect(proxy({ method: 'TRACE' as never, path: '/x' })).rejects.toThrow(
      /invalid api request/
    )
  })

  it('returns non-JSON bodies as text and reports an unreachable sidecar clearly', async () => {
    const textFetch = vi.fn(
      async () => new Response('plain', { status: 500 })
    ) as unknown as typeof fetch
    expect(
      await createApiProxy({ baseUrl: BASE, token: TOKEN, fetchImpl: textFetch })({
        method: 'GET',
        path: '/x'
      })
    ).toEqual({
      status: 500,
      body: 'plain'
    })
    const down = vi.fn(async () => {
      throw new Error('ECONNREFUSED')
    }) as unknown as typeof fetch
    await expect(
      createApiProxy({ baseUrl: BASE, token: TOKEN, fetchImpl: down })({
        method: 'GET',
        path: '/x'
      })
    ).rejects.toThrow(/sidecar unreachable/)
  })

  it('returns PDF responses as base64 so bytes survive IPC', async () => {
    const bytes = new Uint8Array([37, 80, 68, 70, 0, 255, 128])
    const f = vi.fn(
      async () =>
        new Response(bytes, { status: 200, headers: { 'content-type': 'application/pdf' } })
    ) as unknown as typeof fetch
    const proxy = createApiProxy({ baseUrl: BASE, token: TOKEN, fetchImpl: f })
    const res = await proxy({ method: 'GET', path: '/library/documents/1/file' })
    expect(res.status).toBe(200)
    expect(res.body).toEqual({
      contentType: 'application/pdf',
      base64: Buffer.from(bytes).toString('base64')
    })
  })
})
