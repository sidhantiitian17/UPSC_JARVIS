import type { ApiRequest, ApiResponse } from '@jarvis/shared'

const METHODS = new Set(['GET', 'POST', 'PUT', 'DELETE'])
// Absolute path only: no scheme/host, no '//', no '#', no spaces or backslashes.
const SAFE_PATH = /^\/(?!\/)[A-Za-z0-9\-._~/%?=&:,+]*$/

type Options = { baseUrl: string; token: string; fetchImpl: typeof fetch }

function validate(req: ApiRequest): void {
  const ok =
    METHODS.has(req.method) &&
    req.path.length <= 2048 &&
    SAFE_PATH.test(req.path) &&
    !req.path.includes('..')
  if (!ok) throw new Error('invalid api request')
}

/** Forwards renderer requests to the sidecar. The bearer token is added here and never returned. */
export function createApiProxy({ baseUrl, token, fetchImpl }: Options) {
  return async (req: ApiRequest): Promise<ApiResponse> => {
    validate(req)
    let res: Response
    try {
      res = await fetchImpl(`${baseUrl}${req.path}`, {
        method: req.method,
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: req.body === undefined ? undefined : JSON.stringify(req.body)
      })
    } catch {
      throw new Error('sidecar unreachable')
    }
    if ((res.headers.get('content-type') ?? '').startsWith('application/pdf')) {
      const buf = Buffer.from(await res.arrayBuffer())
      return {
        status: res.status,
        body: { contentType: 'application/pdf', base64: buf.toString('base64') }
      }
    }
    const text = await res.text()
    let body: unknown = text === '' ? null : text
    try {
      if (text !== '') body = JSON.parse(text)
    } catch {
      /* keep plain text */
    }
    return { status: res.status, body }
  }
}
