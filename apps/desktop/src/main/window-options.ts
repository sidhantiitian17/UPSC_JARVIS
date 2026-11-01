import type { WebPreferences } from 'electron'

/** Secure defaults for every window that loads our own UI (CLAUDE.md agent rules). */
export function secureWebPreferences(preload: string): WebPreferences {
  return {
    preload,
    contextIsolation: true,
    sandbox: true,
    nodeIntegration: false,
    webSecurity: true
  }
}

/** Only https links may leave the app (opened in the system browser); everything else is denied. */
export function isAllowedExternalUrl(url: string): boolean {
  try {
    return new URL(url).protocol === 'https:'
  } catch {
    return false
  }
}
