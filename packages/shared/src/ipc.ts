/** Types for the renderer <-> main <-> sidecar bridge (the token never reaches the renderer). */
export type ApiMethod = 'GET' | 'POST' | 'PUT' | 'DELETE'

export type ApiRequest = { method: ApiMethod; path: string; body?: unknown }
export type ApiResponse = { status: number; body: unknown }
export type SidecarState = { ready: boolean; error?: string }

/** Secrets live encrypted in the main process (Electron safeStorage); the renderer can only write/delete. */
export type SecretsApi = {
  set: (name: string, value: string) => Promise<void>
  delete: (name: string) => Promise<void>
  names: () => Promise<string[]>
}
