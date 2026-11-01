import type { ApiRequest, ApiResponse, SecretsApi, SidecarState } from '@jarvis/shared'

declare global {
  interface Window {
    jarvis: {
      platform: string
      api: (req: ApiRequest) => Promise<ApiResponse>
      status: () => Promise<SidecarState>
      secrets: SecretsApi
      pickFolder: () => Promise<string | null>
      pickPdf: () => Promise<string | null>
      pathForFile: (file: File) => string
    }
  }
}

export {}
