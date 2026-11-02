/**
 * Pure, time-based focus timer. It never counts ticks: every function takes `now` (ms), so a throttled
 * or suspended renderer cannot drift. Pausing stops the clock; resuming moves the end forward.
 */
export type TimerKind = 'focus' | 'break'

export type TimerState =
  | { status: 'idle' }
  | {
      status: 'running'
      kind: TimerKind
      totalMs: number
      endsAt: number
      segmentStart: number
      /** focus milliseconds banked before the current run segment */
      bankedMs: number
    }
  | {
      status: 'paused'
      kind: TimerKind
      totalMs: number
      remainingMs: number
      bankedMs: number
      reason: 'user' | 'idle'
    }
  | { status: 'expired'; kind: TimerKind; totalMs: number; focusedMs: number }

export const IDLE: TimerState = { status: 'idle' }

export function start(kind: TimerKind, totalMs: number, now: number): TimerState {
  return { status: 'running', kind, totalMs, endsAt: now + totalMs, segmentStart: now, bankedMs: 0 }
}

const segmentFocus = (s: Extract<TimerState, { status: 'running' }>, at: number): number =>
  s.kind === 'focus' ? Math.max(0, Math.min(at, s.endsAt) - s.segmentStart) : 0

export function tick(s: TimerState, now: number): TimerState {
  if (s.status !== 'running' || now < s.endsAt) return s
  return {
    status: 'expired',
    kind: s.kind,
    totalMs: s.totalMs,
    focusedMs: s.bankedMs + segmentFocus(s, s.endsAt)
  }
}

/** `at` is when the clock should stop (for idle pauses: when the owner went idle, not when it was noticed). */
export function pause(s: TimerState, at: number, reason: 'user' | 'idle'): TimerState {
  if (s.status !== 'running') return s
  const stopAt = Math.max(at, s.segmentStart)
  return {
    status: 'paused',
    kind: s.kind,
    totalMs: s.totalMs,
    remainingMs: Math.max(0, s.endsAt - stopAt),
    bankedMs: s.bankedMs + segmentFocus(s, stopAt),
    reason
  }
}

export function resume(s: TimerState, now: number): TimerState {
  if (s.status !== 'paused') return s
  return {
    status: 'running',
    kind: s.kind,
    totalMs: s.totalMs,
    endsAt: now + s.remainingMs,
    segmentStart: now,
    bankedMs: s.bankedMs
  }
}

export const stop = (): TimerState => IDLE

export function remainingMs(s: TimerState, now: number): number {
  if (s.status === 'running') return Math.max(0, s.endsAt - now)
  if (s.status === 'paused') return s.remainingMs
  return 0
}

export function focusedSeconds(s: TimerState, now: number): number {
  switch (s.status) {
    case 'running':
      return Math.floor((s.bankedMs + segmentFocus(s, now)) / 1000)
    case 'paused':
      return Math.floor(s.bankedMs / 1000)
    case 'expired':
      return Math.floor(s.focusedMs / 1000)
    default:
      return 0
  }
}

export function formatClock(ms: number): string {
  const total = Math.ceil(ms / 1000)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
