import type { WindowInfo } from '@jarvis/shared'

/** Foreground window through `active-win` (MIT, pinned), loaded lazily so a missing binary never stops the app. */
export async function readActiveWindow(): Promise<WindowInfo | undefined> {
  const { activeWindow } = await import('active-win')
  const w = await activeWindow({ accessibilityPermission: false, screenRecordingPermission: false })
  if (!w) return undefined
  return { app: w.owner.name, title: w.title, path: w.owner.path }
}
