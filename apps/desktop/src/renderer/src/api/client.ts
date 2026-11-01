import type { ApiMethod, components } from '@jarvis/shared'

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown
  ) {
    super(`API error ${status}`)
  }
}

/** The sidecar needs a few seconds to boot; screens that open at launch wait instead of failing. */
export const startupRetry = { tries: 60, delayMs: 500 }

const notReady = (res: { status: number; body: unknown }): boolean =>
  res.status === 503 && (res.body as { error?: string } | null)?.error === 'sidecar-not-ready'

/** Calls the sidecar through the preload bridge (main adds the token). */
export async function api<T>(method: ApiMethod, path: string, body?: unknown): Promise<T> {
  let res = await window.jarvis.api({ method, path, body })
  for (let i = 0; i < startupRetry.tries && notReady(res); i++) {
    await new Promise((r) => setTimeout(r, startupRetry.delayMs))
    res = await window.jarvis.api({ method, path, body })
  }
  if (res.status < 200 || res.status >= 300) throw new ApiError(res.status, res.body)
  return res.body as T
}

export const getHealth = (): Promise<components['schemas']['Health']> => api('GET', '/health')

type Schemas = components['schemas']

export const getSettings = (): Promise<Schemas['SettingsOut']> => api('GET', '/settings')
export const putSettings = (body: Schemas['SettingsIn']): Promise<Schemas['SettingsOut']> =>
  api('PUT', '/settings', body)
export const testAi = (): Promise<Schemas['AiTestOut']> => api('POST', '/llm/test')

export type SyllabusNode = Schemas['SyllabusNodeOut']
export const getSyllabusTree = (): Promise<SyllabusNode[]> => api('GET', '/syllabus/tree')
export const reloadSyllabus = (): Promise<Schemas['ReloadOut']> => api('POST', '/syllabus/reload')
