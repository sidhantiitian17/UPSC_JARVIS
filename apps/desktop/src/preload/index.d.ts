import type {
  ApiRequest,
  ApiResponse,
  FocusApi,
  PetApi,
  SecretsApi,
  SidecarState
} from '@jarvis/shared'

declare global {
  interface Window {
    jarvis: {
      platform: string
      api: (req: ApiRequest) => Promise<ApiResponse>
      status: () => Promise<SidecarState>
      secrets: SecretsApi
      pet: PetApi
      focus: FocusApi
      pickFolder: () => Promise<string | null>
      pickPdf: () => Promise<string | null>
      idleSeconds: () => Promise<number>
      pathForFile: (file: File) => string
    }
  }
}

export {}
