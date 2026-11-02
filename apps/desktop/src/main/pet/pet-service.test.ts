// @vitest-environment node
import { describe, expect, it, vi } from 'vitest'
import { createPetService, type PetTransport } from './pet-service'

function fakeTransport(over: Partial<PetTransport> = {}): PetTransport & {
  calls: { say: string[]; react: string[] }
} {
  const calls = { say: [] as string[], react: [] as string[] }
  return {
    calls,
    react: over.react ?? (async (r) => void calls.react.push(r)),
    say: over.say ?? (async (t) => void calls.say.push(t)),
    status: over.status ?? (async () => ({ available: true }))
  }
}

function setup(
  over: Partial<PetTransport> = {},
  mode: 'coach' | 'strict' | 'silent' = 'coach'
): {
  service: ReturnType<typeof createPetService>
  transport: ReturnType<typeof fakeTransport>
  advance: (ms: number) => number
} {
  const transport = fakeTransport(over)
  let now = 1_000_000
  const service = createPetService({ transport, now: () => now })
  service.setMode(mode)
  return { service, transport, advance: (ms: number) => (now += ms) }
}

describe('pet service', () => {
  it('sends a reaction and a message for a known event', async () => {
    const { service, transport } = setup()
    expect(await service.event('session_start')).toBe(true)
    expect(transport.calls.react).toEqual(['working'])
    expect(transport.calls.say).toHaveLength(1)
    expect(transport.calls.say[0].length).toBeLessThanOrEqual(140)
  })

  it('silent mode reacts but never speaks', async () => {
    const { service, transport } = setup({}, 'silent')
    await service.event('gate_pass', { retentionPct: 90 })
    expect(transport.calls.react).toEqual(['celebrating'])
    expect(transport.calls.say).toEqual([])
  })

  it('uses the mode set by the owner', async () => {
    const { service, transport } = setup({}, 'strict')
    await service.event('gate_pass', { retentionPct: 80 })
    expect(transport.calls.say[0]).toBe('Gate pass. Retention 80%.')
    service.setMode('coach')
    await service.event('gate_pass', { retentionPct: 80 })
    expect(transport.calls.say[1]).toContain('80%')
    expect(transport.calls.say[1]).not.toBe(transport.calls.say[0])
  })

  it('rejects unknown events, unknown modes and nonsense context without calling the pet', async () => {
    const { service, transport } = setup()
    expect(await service.event('explode' as never)).toBe(false)
    service.setMode('angry' as never)
    expect(service.getMode()).toBe('coach')
    expect(await service.event('gate_pass', { retentionPct: 'high' } as never)).toBe(true)
    expect(transport.calls.say[0]).not.toContain('high')
    expect(transport.calls.react).toEqual(['celebrating'])
  })

  it('degrades silently when OpenPets is not running', async () => {
    const boom = vi.fn(async () => {
      throw new Error('connect ENOENT openpets pipe')
    })
    const { service } = setup({ react: boom, say: boom })
    await expect(service.event('session_start')).resolves.toBe(false)
    expect(await service.status()).toEqual({ available: false, mode: 'coach' })
  })

  it('reports availability and the mode in status', async () => {
    const { service } = setup()
    expect(await service.status()).toEqual({ available: true, mode: 'coach' })
  })

  it('status never throws', async () => {
    const { service } = setup({
      status: async () => {
        throw new Error('down')
      }
    })
    expect(await service.status()).toEqual({ available: false, mode: 'coach' })
  })

  it('rate limits idle and distraction nudges but not celebrations', async () => {
    const { service, transport, advance } = setup()
    expect(await service.event('distraction')).toBe(true)
    advance(60_000)
    expect(await service.event('distraction')).toBe(false)
    advance(5 * 60_000)
    expect(await service.event('distraction')).toBe(true)
    expect(await service.event('idle')).toBe(true)
    advance(1000)
    expect(await service.event('idle')).toBe(false)
    expect(await service.event('level_up')).toBe(true)
    expect(await service.event('level_up')).toBe(true)
    expect(transport.calls.say.length).toBe(5)
  })

  it('does not speak the same message twice in a row within 30 seconds', async () => {
    const { service, transport, advance } = setup()
    await service.event('session_start')
    advance(5_000)
    await service.event('session_start')
    expect(transport.calls.say).toHaveLength(1)
    advance(40_000)
    await service.event('session_start')
    expect(transport.calls.say).toHaveLength(2)
  })

  it('test() sends a friendly hello and reports whether it was shown', async () => {
    const { service, transport } = setup()
    expect(await service.test()).toBe(true)
    expect(transport.calls.say[0]).toMatch(/JARVIS/)
    const dead = setup({
      say: async () => {
        throw new Error('down')
      }
    })
    expect(await dead.service.test()).toBe(false)
  })
})
