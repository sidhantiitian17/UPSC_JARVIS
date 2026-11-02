import { contextBridge, ipcRenderer, webUtils } from 'electron'
import type {
  ApiRequest,
  ApiResponse,
  FocusApi,
  PetApi,
  SecretsApi,
  SidecarState
} from '@jarvis/shared'

// Sandbox-safe bridge. The renderer never sees the sidecar URL or token: main proxies every call.
// Secrets are write-only from the renderer: main stores them encrypted and forwards them to the sidecar.
const secrets: SecretsApi = {
  set: (name, value) => ipcRenderer.invoke('secrets:set', name, value),
  delete: (name) => ipcRenderer.invoke('secrets:delete', name),
  names: () => ipcRenderer.invoke('secrets:names')
}

const pet: PetApi = {
  event: (name, ctx) => ipcRenderer.invoke('pet:event', name, ctx),
  setMode: (mode) => ipcRenderer.invoke('pet:setMode', mode),
  status: () => ipcRenderer.invoke('pet:status'),
  test: () => ipcRenderer.invoke('pet:test')
}

const focus: FocusApi = {
  setEnabled: (on) => ipcRenderer.invoke('focus:setEnabled', on),
  setSession: (on) => ipcRenderer.invoke('focus:setSession', on)
}

contextBridge.exposeInMainWorld('jarvis', {
  pet,
  focus,
  platform: process.platform,
  api: (req: ApiRequest): Promise<ApiResponse> => ipcRenderer.invoke('api:request', req),
  status: (): Promise<SidecarState> => ipcRenderer.invoke('api:status'),
  secrets,
  pickFolder: (): Promise<string | null> => ipcRenderer.invoke('dialog:pickFolder'),
  idleSeconds: (): Promise<number> => ipcRenderer.invoke('system:idleSeconds'),
  pickPdf: (): Promise<string | null> => ipcRenderer.invoke('dialog:pickPdf'),
  // Dropped files: the sandboxed renderer cannot read paths itself, so ask Electron's webUtils.
  pathForFile: (file: File): string => webUtils.getPathForFile(file)
})
