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

/** Pet companion bridge. Every call is best-effort: the pet being absent must never break studying. */
export type PetApi = {
  event: (name: string, ctx?: { retentionPct?: number; level?: number }) => Promise<boolean>
  setMode: (mode: string) => Promise<void>
  status: () => Promise<{ available: boolean; mode: string }>
  test: () => Promise<boolean>
}

/** Focus Guard bridge: the renderer only says whether the guard is on and whether a focus block is running. */
export type FocusApi = {
  setEnabled: (on: boolean) => Promise<void>
  setSession: (on: boolean) => Promise<void>
}
