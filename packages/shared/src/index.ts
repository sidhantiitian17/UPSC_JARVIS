export const APP_NAME = 'UPSC JARVIS'

/** Names of every top-level screen, in sidebar order (single source of truth for UI and tests). */
export const SCREENS = [
  'today',
  'study',
  'syllabus',
  'pyq',
  'mains',
  'ca',
  'interview',
  'browser',
  'insights',
  'settings'
] as const
export type ScreenId = (typeof SCREENS)[number]

export type {
  ApiMethod,
  ApiRequest,
  ApiResponse,
  FocusApi,
  PetApi,
  SecretsApi,
  SidecarState
} from './ipc'
export type { components, paths } from './api'

export * from './pet'
export * from './focus'
