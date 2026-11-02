// @vitest-environment node
import { describe, expect, it, vi } from 'vitest'
import { createFocusGuard, type Sample } from './focus-guard'

type Win = { app: string; title?: string; path?: string } | undefined

function setup(opts: { windows?: Win[]; postFails?: boolean } = {}): {
  guard: ReturnType<typeof createFocusGuard>
  posted: Sample[][]
  nudges: { count: number }
  setWindow: (w: Win) => void
} {
  let current: Win = { app: 'Adobe Acrobat', title: 'book.pdf' }
  const queue = [...(opts.windows ?? [])]
  const posted: Sample[][] = []
  const nudges = { count: 0 }
  const guard = createFocusGuard({
    activeWindow: async () => (queue.length ? queue.shift() : current),
    postSamples: async (s) => {
      if (opts.postFails) throw new Error('sidecar down')
      posted.push(s)
    },
    onDistraction: () => void nudges.count++,
    now: () => new Date('2026-11-05T10:00:00Z').getTime()
  })
  return { guard, posted, nudges, setWindow: (w) => void (current = w) }
}

const ticks = async (g: ReturnType<typeof createFocusGuard>, n: number): Promise<void> => {
  for (let i = 0; i < n; i++) await g.tick()
}

describe('Focus Guard', () => {
  it('samples nothing while it is off', async () => {
    const { guard, posted } = setup()
    guard.setSessionActive(true)
    await ticks(guard, 20)
    await guard.flush()
    expect(posted).toEqual([])
  })

  it('samples nothing when no focus block is running', async () => {
    const { guard, posted } = setup()
    guard.setEnabled(true)
    await ticks(guard, 20)
    await guard.flush()
    expect(posted).toEqual([])
  })

  it('samples study windows during a focus block and posts only category and app', async () => {
    const { guard, posted } = setup()
    guard.setEnabled(true)
    guard.setSessionActive(true)
    await ticks(guard, 3)
    await guard.flush()
    expect(posted).toHaveLength(1)
    expect(posted[0]).toHaveLength(3)
    expect(posted[0][0]).toEqual({
      ts: '2026-11-05T10:00:00.000Z',
      category: 'study',
      app: 'Adobe Acrobat'
    })
    expect(Object.keys(posted[0][0]).sort()).toEqual(['app', 'category', 'ts'])
  })

  it('never includes window titles in what it posts', async () => {
    const { guard, posted, setWindow } = setup()
    setWindow({ app: 'Google Chrome', title: 'My private bank statement' })
    guard.setEnabled(true)
    guard.setSessionActive(true)
    await ticks(guard, 2)
    await guard.flush()
    expect(JSON.stringify(posted)).not.toContain('private')
    expect(JSON.stringify(posted)).not.toContain('bank')
  })

  it('skips JARVIS, OpenPets and unreadable windows', async () => {
    const { guard, posted } = setup({
      windows: [
        { app: 'UPSC JARVIS' },
        { app: 'openpets' },
        undefined,
        { app: 'Notepad', title: 'x' }
      ]
    })
    guard.setEnabled(true)
    guard.setSessionActive(true)
    await ticks(guard, 4)
    await guard.flush()
    expect(posted[0].map((s) => s.app)).toEqual(['Notepad'])
  })

  it('flushes automatically in batches and when the focus block ends', async () => {
    const { guard, posted } = setup()
    guard.setEnabled(true)
    guard.setSessionActive(true)
    await ticks(guard, 6)
    expect(posted.length).toBe(1)
    await ticks(guard, 2)
    guard.setSessionActive(false)
    await vi.waitFor(() => expect(posted.flat().length).toBe(8))
  })

  it('nudges once for a two-minute stretch of distraction and again only after a break from it', async () => {
    const { guard, nudges, setWindow } = setup()
    setWindow({ app: 'Steam' })
    guard.setEnabled(true)
    guard.setSessionActive(true)
    await ticks(guard, 23)
    expect(nudges.count).toBe(0)
    await ticks(guard, 1)
    expect(nudges.count).toBe(1)
    await ticks(guard, 40)
    expect(nudges.count).toBe(1)
    setWindow({ app: 'Adobe Acrobat' })
    await ticks(guard, 1)
    setWindow({ app: 'Steam' })
    await ticks(guard, 24)
    expect(nudges.count).toBe(2)
  })

  it('does not throw when the sidecar is down: samples are dropped, studying continues', async () => {
    const { guard } = setup({ postFails: true })
    guard.setEnabled(true)
    guard.setSessionActive(true)
    await ticks(guard, 8)
    await expect(guard.flush()).resolves.toBeUndefined()
  })

  it('turning it off clears anything not yet sent', async () => {
    const { guard, posted } = setup()
    guard.setEnabled(true)
    guard.setSessionActive(true)
    await ticks(guard, 3)
    guard.setEnabled(false)
    await guard.flush()
    expect(posted).toEqual([])
  })
})
