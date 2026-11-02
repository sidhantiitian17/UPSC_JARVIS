import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TimerContext, type TimerApi } from './timer-context'
import { TimerChip } from './timer-chip'

const base: TimerApi = {
  state: { status: 'idle' },
  clock: '50:00',
  focusedSeconds: 0,
  minutes: { focus: 50, break: 10 },
  startFocus: vi.fn(),
  startBreak: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  stop: vi.fn()
}
const running = (over: Partial<TimerApi> = {}): TimerApi => ({
  ...base,
  state: {
    status: 'running',
    kind: 'focus',
    totalMs: 3_000_000,
    endsAt: 1,
    segmentStart: 0,
    bankedMs: 0
  },
  clock: '31:05',
  ...over
})

describe('TimerChip', () => {
  it('shows nothing while idle', () => {
    const { container } = render(
      <TimerContext.Provider value={base}>
        <TimerChip />
      </TimerContext.Provider>
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('shows the countdown and lets the owner pause', async () => {
    const pause = vi.fn()
    render(
      <TimerContext.Provider value={running({ pause })}>
        <TimerChip />
      </TimerContext.Provider>
    )
    expect(screen.getByRole('timer', { name: /focus timer/i })).toHaveTextContent('31:05')
    await userEvent.click(screen.getByRole('button', { name: /pause timer/i }))
    expect(pause).toHaveBeenCalled()
  })

  it('explains an idle pause and offers to resume', async () => {
    const resume = vi.fn()
    const paused = running({
      state: {
        status: 'paused',
        kind: 'focus',
        totalMs: 3_000_000,
        remainingMs: 1,
        bankedMs: 0,
        reason: 'idle'
      },
      resume
    })
    render(
      <TimerContext.Provider value={paused}>
        <TimerChip />
      </TimerContext.Provider>
    )
    expect(screen.getByText(/paused: you were away/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /resume timer/i }))
    expect(resume).toHaveBeenCalled()
  })

  it('announces that time is up', () => {
    render(
      <TimerContext.Provider
        value={running({
          state: { status: 'expired', kind: 'focus', totalMs: 1, focusedMs: 1 },
          clock: '00:00'
        })}
      >
        <TimerChip />
      </TimerContext.Provider>
    )
    expect(screen.getByRole('timer')).toHaveTextContent(/time is up/i)
  })
})
