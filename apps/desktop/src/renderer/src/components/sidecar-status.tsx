import { useEffect, useState } from 'react'
import type { SidecarState } from '@jarvis/shared'

/** Banner shown until the local engine (sidecar) is ready; says why if it failed. Hidden when ready. */
export function SidecarStatus({ pollMs = 1500 }: { pollMs?: number }): React.JSX.Element | null {
  const [state, setState] = useState<SidecarState | null>(null)

  useEffect(() => {
    if (!window.jarvis?.status) return
    let stopped = false
    let timer: ReturnType<typeof setTimeout>
    const tick = async (): Promise<void> => {
      const s = await window.jarvis
        .status()
        .catch((e: unknown) => ({ ready: false, error: String(e) }))
      if (stopped) return
      setState(s)
      if (!s.ready && !s.error) timer = setTimeout(tick, pollMs)
    }
    void tick()
    return () => {
      stopped = true
      clearTimeout(timer)
    }
  }, [pollMs])

  if (!state || state.ready) return null
  if (state.error) {
    return (
      <div role="alert" className="mb-4 rounded-lg border border-danger p-3 text-sm text-danger">
        Local engine failed to start: {state.error}. Check that Python tooling (uv) is installed,
        then restart the app.
      </div>
    )
  }
  return (
    <div role="status" className="mb-4 rounded-lg border border-line p-3 text-sm text-muted">
      Starting local engine…
    </div>
  )
}
