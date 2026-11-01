import type { ApiRequest, ApiResponse, SidecarState } from '@jarvis/shared'

declare global {
  interface Window {
    jarvis: {
      platform: string
      api: (req: ApiRequest) => Promise<ApiResponse>
      status: () => Promise<SidecarState>
    }
  }
}

export {}
