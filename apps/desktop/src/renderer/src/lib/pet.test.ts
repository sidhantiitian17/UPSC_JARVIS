import { afterEach, describe, expect, it, vi } from 'vitest'
import { petEvent } from './pet'

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('petEvent', () => {
  it('forwards the event and context to the bridge', () => {
    const event = vi.fn(async () => true)
    ;(window as unknown as { jarvis: unknown }).jarvis = { pet: { event } }
    petEvent('gate_pass', { retentionPct: 85 })
    expect(event).toHaveBeenCalledWith('gate_pass', { retentionPct: 85 })
  })

  it('does nothing when there is no bridge', () => {
    expect(() => petEvent('idle')).not.toThrow()
    ;(window as unknown as { jarvis: unknown }).jarvis = {}
    expect(() => petEvent('idle')).not.toThrow()
  })

  it('swallows a rejected or throwing pet call', async () => {
    ;(window as unknown as { jarvis: unknown }).jarvis = {
      pet: { event: vi.fn(async () => Promise.reject(new Error('down'))) }
    }
    expect(() => petEvent('level_up')).not.toThrow()
    ;(window as unknown as { jarvis: unknown }).jarvis = {
      pet: {
        event: () => {
          throw new Error('sync boom')
        }
      }
    }
    expect(() => petEvent('level_up')).not.toThrow()
    await Promise.resolve()
  })
})
