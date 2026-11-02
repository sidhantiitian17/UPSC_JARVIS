import { describe, expect, it } from 'vitest'
import {
  IDLE,
  focusedSeconds,
  pause,
  remainingMs,
  resume,
  start,
  stop,
  tick,
  type TimerState
} from './timer-machine'

const MIN = 60_000

describe('timer state machine', () => {
  it('starts a focus block with the full duration remaining', () => {
    const s = start('focus', 50 * MIN, 1000)
    expect(s.status).toBe('running')
    expect(remainingMs(s, 1000)).toBe(50 * MIN)
  })

  it('keeps running until the end, then expires with all minutes focused', () => {
    let s: TimerState = start('focus', 50 * MIN, 0)
    s = tick(s, 49 * MIN + 59_000)
    expect(s.status).toBe('running')
    expect(remainingMs(s, 49 * MIN + 59_000)).toBe(1000)
    s = tick(s, 50 * MIN)
    expect(s.status).toBe('expired')
    expect(focusedSeconds(s, 51 * MIN)).toBe(3000)
  })

  it('pause freezes the clock and resume continues from the remaining time', () => {
    let s: TimerState = start('focus', 50 * MIN, 0)
    s = pause(s, 10 * MIN, 'user')
    expect(s.status).toBe('paused')
    expect(remainingMs(s, 99 * MIN)).toBe(40 * MIN)
    s = resume(s, 30 * MIN)
    expect(remainingMs(s, 30 * MIN)).toBe(40 * MIN)
    expect(focusedSeconds(s, 40 * MIN)).toBe(20 * 60)
  })

  it('does not count paused time as focused time', () => {
    let s: TimerState = start('focus', 50 * MIN, 0)
    s = pause(s, 5 * MIN, 'user')
    s = resume(s, 25 * MIN)
    s = tick(s, 25 * MIN + 45 * MIN)
    expect(s.status).toBe('expired')
    expect(focusedSeconds(s, 999 * MIN)).toBe(50 * 60)
  })

  it('an idle pause is backdated to when the owner stopped, not when idleness was detected', () => {
    let s: TimerState = start('focus', 50 * MIN, 0)
    // detected at minute 10, idle for 3 minutes => the clock should stop at minute 7
    s = pause(s, 10 * MIN - 3 * MIN, 'idle')
    expect(s.status === 'paused' && s.reason).toBe('idle')
    expect(remainingMs(s, 10 * MIN)).toBe(43 * MIN)
    expect(focusedSeconds(s, 10 * MIN)).toBe(7 * 60)
  })

  it('ignores pause when not running and resume when not paused', () => {
    expect(pause(IDLE, 0, 'user')).toBe(IDLE)
    expect(resume(IDLE, 0)).toBe(IDLE)
    const running = start('focus', MIN, 0)
    expect(resume(running, 5)).toBe(running)
  })

  it('stop returns to idle from any state', () => {
    expect(stop()).toBe(IDLE)
  })

  it('a break counts down but never adds focused time', () => {
    let s: TimerState = start('break', 10 * MIN, 0)
    s = tick(s, 10 * MIN)
    expect(s.status).toBe('expired')
    expect(focusedSeconds(s, 11 * MIN)).toBe(0)
  })

  it('tick on idle or paused leaves the state untouched', () => {
    const paused = pause(start('focus', MIN, 0), 10, 'user')
    expect(tick(paused, 5 * MIN)).toBe(paused)
    expect(tick(IDLE, 5 * MIN)).toBe(IDLE)
  })
})
