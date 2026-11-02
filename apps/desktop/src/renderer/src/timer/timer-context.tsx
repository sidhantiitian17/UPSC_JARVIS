/* eslint-disable react-refresh/only-export-components -- the provider and its hook belong together */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getSettings } from '../api/client'
import { petEvent } from '../lib/pet'
import {
  IDLE,
  focusedSeconds,
  formatClock,
  pause as pauseState,
  remainingMs,
  resume as resumeState,
  start,
  stop as stopState,
  tick,
  type TimerState
} from './timer-machine'

export const IDLE_LIMIT_SECONDS = 120
const IDLE_POLL_MS = 5000

export type TimerApi = {
  state: TimerState
  /** mm:ss of the time left (or the configured block length while idle) */
  clock: string
  focusedSeconds: number
  minutes: { focus: number; break: number }
  startFocus: () => void
  startBreak: () => void
  pause: () => void
  resume: () => void
  stop: () => void
}

const noop = (): void => undefined
const INERT: TimerApi = {
  state: IDLE,
  clock: '50:00',
  focusedSeconds: 0,
  minutes: { focus: 50, break: 10 },
  startFocus: noop,
  startBreak: noop,
  pause: noop,
  resume: noop,
  stop: noop
}

export const TimerContext = createContext<TimerApi>(INERT)
export const useTimer = (): TimerApi => useContext(TimerContext)

export function TimerProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const [state, setState] = useState<TimerState>(IDLE)
  const [now, setNow] = useState(() => Date.now())
  const [minutes, setMinutes] = useState({ focus: 50, break: 10 })

  useEffect(() => {
    let alive = true
    getSettings()
      .then((s) => alive && setMinutes({ focus: s.focus_minutes, break: s.break_minutes }))
      .catch(() => undefined) // keep the 50/10 defaults if the service is not reachable
    return () => {
      alive = false
    }
  }, [])

  const running = state.status === 'running'
  const focusRunning = running && state.kind === 'focus'
  useEffect(() => {
    // Focus Guard watches the foreground window only while a focus block is actually running.
    void Promise.resolve(window.jarvis?.focus?.setSession(focusRunning)).catch(() => undefined)
  }, [focusRunning])
  useEffect(() => {
    if (!running) return
    const id = setInterval(() => {
      const t = Date.now()
      setNow(t)
      setState((s) => tick(s, t))
    }, 250)
    return () => clearInterval(id)
  }, [running])

  useEffect(() => {
    if (!running) return
    const id = setInterval(async () => {
      const probe = window.jarvis?.idleSeconds
      if (typeof probe !== 'function') return
      try {
        const idle = await probe()
        if (idle >= IDLE_LIMIT_SECONDS) {
          setState((s) => pauseState(s, Date.now() - idle * 1000, 'idle'))
          petEvent('idle')
        }
      } catch {
        /* idle detection is best-effort */
      }
    }, IDLE_POLL_MS)
    return () => clearInterval(id)
  }, [running])

  const doPause = useCallback(() => {
    setNow(Date.now())
    setState((s) => pauseState(s, Date.now(), 'user'))
  }, [])
  const doResume = useCallback(() => {
    setNow(Date.now())
    setState((s) => resumeState(s, Date.now()))
  }, [])

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key !== ' ' || e.repeat) return
      const tag = (e.target as HTMLElement | null)?.tagName
      if (tag && ['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(tag)) return
      if (state.status === 'running') {
        e.preventDefault()
        doPause()
      } else if (state.status === 'paused') {
        e.preventDefault()
        doResume()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [state.status, doPause, doResume])

  const api = useMemo<TimerApi>(
    () => ({
      state,
      clock: formatClock(
        state.status === 'idle' ? minutes.focus * 60_000 : remainingMs(state, now)
      ),
      focusedSeconds: focusedSeconds(state, now),
      minutes,
      startFocus: () => {
        const t = Date.now()
        setNow(t)
        setState(start('focus', minutes.focus * 60_000, t))
      },
      startBreak: () => {
        const t = Date.now()
        setNow(t)
        setState(start('break', minutes.break * 60_000, t))
      },
      pause: doPause,
      resume: doResume,
      stop: () => setState(stopState())
    }),
    [state, now, minutes, doPause, doResume]
  )

  return <TimerContext.Provider value={api}>{children}</TimerContext.Provider>
}
