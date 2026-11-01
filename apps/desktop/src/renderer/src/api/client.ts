import type { ApiMethod, components } from '@jarvis/shared'

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown
  ) {
    super(`API error ${status}`)
  }
}

/** Calls the sidecar through the preload bridge (main adds the token). */
export async function api<T>(method: ApiMethod, path: string, body?: unknown): Promise<T> {
  const res = await window.jarvis.api({ method, path, body })
  if (res.status < 200 || res.status >= 300) throw new ApiError(res.status, res.body)
  return res.body as T
}

export const getHealth = (): Promise<components['schemas']['Health']> => api('GET', '/health')

type Schemas = components['schemas']

export const getSettings = (): Promise<Schemas['SettingsOut']> => api('GET', '/settings')
export const putSettings = (body: Schemas['SettingsIn']): Promise<Schemas['SettingsOut']> =>
  api('PUT', '/settings', body)
export const testAi = (): Promise<Schemas['AiTestOut']> => api('POST', '/llm/test')
