import { classifyWindow, type FocusCategory, type WindowInfo } from '@jarvis/shared'

export type Sample = { ts: string; category: FocusCategory; app: string }

export const SAMPLE_INTERVAL_MS = 5000
const BATCH = 6 // post about every 30 seconds
const DISTRACTION_STREAK = 24 // 24 samples x 5 s = 2 minutes

type Deps = {
  activeWindow: () => Promise<WindowInfo | undefined>
  postSamples: (samples: Sample[]) => Promise<void>
  onDistraction: () => void
  now?: () => number
}

/**
 * Opt-in, local focus watcher. It samples only while it is enabled AND a focus block is running,
 * keeps window titles in memory just long enough to classify them, and posts only {ts, category, app}.
 */
export function createFocusGuard({
  activeWindow,
  postSamples,
  onDistraction,
  now = Date.now
}: Deps): {
  setEnabled: (on: boolean) => void
  setSessionActive: (on: boolean) => void
  tick: () => Promise<void>
  flush: () => Promise<void>
  start: () => void
  stop: () => void
} {
  let enabled = false
  let sessionActive = false
  let buffer: Sample[] = []
  let streak = 0
  let nudged = false
  let timer: ReturnType<typeof setInterval> | null = null

  const flush = async (): Promise<void> => {
    if (buffer.length === 0) return
    const batch = buffer
    buffer = []
    try {
      await postSamples(batch)
    } catch {
      /* the sidecar is down: drop this batch, studying must never be interrupted */
    }
  }

  const resetStreak = (): void => {
    streak = 0
    nudged = false
  }

  return {
    setEnabled(on) {
      enabled = on
      if (!on) {
        buffer = []
        resetStreak()
      }
    },
    setSessionActive(on) {
      const ended = sessionActive && !on
      sessionActive = on
      if (!on) resetStreak()
      if (ended) void flush()
    },
    async tick() {
      if (!enabled || !sessionActive) return
      let win: WindowInfo | undefined
      try {
        win = await activeWindow()
      } catch {
        return
      }
      if (!win) return
      const category = classifyWindow(win)
      if (category === null) return // JARVIS / OpenPets: not sampled, streak unchanged
      buffer.push({ ts: new Date(now()).toISOString(), category, app: win.app.slice(0, 80) })
      if (category === 'distraction') {
        streak += 1
        if (streak >= DISTRACTION_STREAK && !nudged) {
          nudged = true
          onDistraction()
        }
      } else {
        resetStreak()
      }
      if (buffer.length >= BATCH) await flush()
    },
    flush,
    start() {
      if (timer) return
      timer = setInterval(() => void this.tick(), SAMPLE_INTERVAL_MS)
    },
    stop() {
      if (timer) clearInterval(timer)
      timer = null
      void flush()
    }
  }
}
