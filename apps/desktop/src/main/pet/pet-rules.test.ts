import { describe, expect, it } from 'vitest'
import {
  PET_EVENTS,
  PET_MAX_SAY,
  PET_MODES,
  PET_REACTIONS,
  SHAME_WORDS,
  petMessage,
  type PetContext
} from '@jarvis/shared'

const CONTEXTS: PetContext[] = [
  {},
  { retentionPct: 85 },
  { level: 3 },
  { retentionPct: 100, level: 12 }
]

describe('pet message rules', () => {
  it.each(PET_EVENTS)('event %s maps to an allowed OpenPets reaction in every mode', (event) => {
    for (const mode of PET_MODES) {
      expect(PET_REACTIONS).toContain(petMessage(event, mode).reaction)
    }
  })

  it('never exceeds 140 characters and never contains a shaming word, in any mode, event or context', () => {
    for (const event of PET_EVENTS)
      for (const mode of PET_MODES)
        for (const ctx of CONTEXTS) {
          const say = petMessage(event, mode, ctx).say
          if (say === undefined) continue
          expect(say.length).toBeLessThanOrEqual(PET_MAX_SAY)
          const lower = say.toLowerCase()
          for (const bad of SHAME_WORDS) expect(lower).not.toContain(bad)
        }
  })

  it('silent mode animates only and never speaks', () => {
    for (const event of PET_EVENTS)
      expect(petMessage(event, 'silent', { retentionPct: 90 }).say).toBeUndefined()
  })

  it('coach and strict both speak, and strict is shorter overall', () => {
    let coach = 0
    let strict = 0
    for (const event of PET_EVENTS) {
      const c = petMessage(event, 'coach').say
      const s = petMessage(event, 'strict').say
      expect(c).toBeTruthy()
      expect(s).toBeTruthy()
      coach += c!.length
      strict += s!.length
    }
    expect(strict).toBeLessThan(coach)
  })

  it('follows the owner rules: restudy after a gate that was not passed, a break when idle, small level-ups', () => {
    expect(petMessage('gate_not_passed', 'coach').say).toMatch(/restudy/i)
    expect(petMessage('gate_not_passed', 'strict').say).toMatch(/restudy/i)
    expect(petMessage('idle', 'coach').say).toMatch(/break/i)
    expect(petMessage('level_up', 'coach', { level: 4 }).say).toContain('4')
    expect(petMessage('level_up', 'coach').say).not.toMatch(/!!|🎉/)
  })

  it('uses the specific numbers it is given', () => {
    expect(petMessage('gate_pass', 'coach', { retentionPct: 85 }).say).toContain('85%')
    expect(petMessage('gate_pass', 'strict', { retentionPct: 85 }).say).toContain('85%')
  })

  it('has at least 20 distinct sample messages for the A5 review', () => {
    const all = new Set<string>()
    for (const event of PET_EVENTS)
      for (const mode of ['coach', 'strict'] as const)
        for (const ctx of CONTEXTS) all.add(petMessage(event, mode, ctx).say ?? '')
    expect(all.size).toBeGreaterThanOrEqual(20)
  })
})
