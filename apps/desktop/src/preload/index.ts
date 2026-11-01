import { contextBridge, ipcRenderer } from 'electron'
import type { ApiRequest, ApiResponse, SidecarState } from '@jarvis/shared'

// Sandbox-safe bridge. The renderer never sees the sidecar URL or token: main proxies every call.
contextBridge.exposeInMainWorld('jarvis', {
  platform: process.platform,
  api: (req: ApiRequest): Promise<ApiResponse> => ipcRenderer.invoke('api:request', req),
  status: (): Promise<SidecarState> => ipcRenderer.invoke('api:status')
})
