import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { TimerProvider, useTimer } from './timer-context'

function Probe(): React.JSX.Element {
  const t = useTimer()
  return (
    <div>
      <output aria-label="clock">{t.clock}</output>
      <output aria-label="status">{t.state.status}</output>
      <output aria-label="focused">{t.focusedSeconds}</output>
      <output aria-label="reason">{t.state.status === 'paused' ? t.state.reason : ''}</output>
      <button onClick={() => t.startFocus()}>start</button>
      <button onClick={() => t.pause()}>pause</button>
      <button onClick={() => t.resume()}>resume</button>
      <button onClick={() => t.stop()}>stop</button>
    </div>
  )
}

function bridge(idle = 0, focus = 25): { idleSeconds: ReturnType<typeof vi.fn> } {
  const idleSeconds = vi.fn(async () => idle)
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api: vi.fn(async () => ({ status: 200, body: { focus_minutes: focus, break_minutes: 5 } })),
    status: async () => ({ ready: true }),
    idleSeconds
  }
  return { idleSeconds }
}

const out = (name: string): string => screen.getByLabelText(name).textContent ?? ''

async function mount(): Promise<void> {
  render(
    <TimerProvider>
      <Probe />
    </TimerProvider>
  )
  await act(async () => {
    await vi.advanceTimersByTimeAsync(10)
  })
}
const advance = (ms: number): Promise<void> =>
  act(async () => {
    await vi.advanceTimersByTimeAsync(ms)
  })

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: false })
})
afterEach(() => {
  vi.useRealTimers()
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('TimerProvider', () => {
  it('uses the configured focus minutes and counts down', async () => {
    bridge(0, 25)
    await mount()
    expect(out('status')).toBe('idle')
    await act(async () => screen.getByText('start').click())
    expect(out('clock')).toBe('25:00')
    await advance(61_000)
    expect(out('clock')).toBe('23:59')
    expect(Number(out('focused'))).toBeGreaterThanOrEqual(60)
  })

  it('expires at zero', async () => {
    bridge(0, 5)
    await mount()
    await act(async () => screen.getByText('start').click())
    await advance(5 * 60_000 + 500)
    expect(out('status')).toBe('expired')
    expect(out('clock')).toBe('00:00')
    expect(out('focused')).toBe('300')
  })

  it('pauses and resumes without counting the pause as focus', async () => {
    bridge(0, 25)
    await mount()
    await act(async () => screen.getByText('start').click())
    await advance(60_000)
    await act(async () => screen.getByText('pause').click())
    await advance(10 * 60_000)
    expect(out('status')).toBe('paused')
    expect(out('focused')).toBe('60')
    await act(async () => screen.getByText('resume').click())
    expect(out('status')).toBe('running')
  })

  it('auto-pauses when the system has been idle for two minutes, backdated to when idleness began', async () => {
    const { idleSeconds } = bridge(0, 25)
    await mount()
    await act(async () => screen.getByText('start').click())
    await advance(4 * 60_000)
    idleSeconds.mockResolvedValue(180)
    await advance(5_000)
    expect(out('status')).toBe('paused')
    expect(out('reason')).toBe('idle')
    // 4:05 elapsed, 3:00 of it idle => about 65s focused
    expect(Number(out('focused'))).toBeLessThanOrEqual(70)
    expect(Number(out('focused'))).toBeGreaterThanOrEqual(55)
  })

  it('does not auto-pause on short idleness', async () => {
    const { idleSeconds } = bridge(0, 25)
    await mount()
    await act(async () => screen.getByText('start').click())
    idleSeconds.mockResolvedValue(30)
    await advance(10_000)
    expect(out('status')).toBe('running')
  })

  it('Space toggles pause and resume outside form fields', async () => {
    bridge(0, 25)
    await mount()
    await act(async () => screen.getByText('start').click())
    await act(async () => {
      document.body.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }))
    })
    expect(out('status')).toBe('paused')
    await act(async () => {
      document.body.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }))
    })
    expect(out('status')).toBe('running')
  })

  it('stop returns to idle', async () => {
    bridge(0, 25)
    await mount()
    await act(async () => screen.getByText('start').click())
    await act(async () => screen.getByText('stop').click())
    expect(out('status')).toBe('idle')
    void userEvent
  })
})
