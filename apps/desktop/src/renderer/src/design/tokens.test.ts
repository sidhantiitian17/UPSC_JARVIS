import { readFileSync } from 'fs'
import { resolve } from 'path'
import { describe, expect, it } from 'vitest'
import { contrastRatio } from '../lib/contrast'
import { tokens } from './tokens'

const css = readFileSync(resolve(__dirname, '../assets/main.css'), 'utf-8').toLowerCase()

describe('design tokens (agents/project/DESIGN.md)', () => {
  it('contrast helper matches known WCAG values', () => {
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 0)
    expect(contrastRatio('#777777', '#ffffff')).toBeGreaterThan(4.4)
    expect(contrastRatio('#777777', '#ffffff')).toBeLessThan(4.6)
  })

  for (const mode of ['dark', 'light'] as const) {
    const t = tokens[mode]
    it(`${mode}: body and muted text meet WCAG AA (4.5:1) on their surfaces`, () => {
      expect(contrastRatio(t.text, t.bg)).toBeGreaterThanOrEqual(4.5)
      expect(contrastRatio(t.text, t.surface)).toBeGreaterThanOrEqual(4.5)
      expect(contrastRatio(t.textMuted, t.bg)).toBeGreaterThanOrEqual(4.5)
      expect(contrastRatio(t.textMuted, t.surface)).toBeGreaterThanOrEqual(4.5)
    })
    it(`${mode}: button text on accent meets AA and accent is visible (3:1) on the background`, () => {
      expect(contrastRatio(t.accentContrast, t.accent)).toBeGreaterThanOrEqual(4.5)
      expect(contrastRatio(t.accent, t.bg)).toBeGreaterThanOrEqual(3)
    })
    it(`${mode}: success, warning and danger are visible (3:1) on the background`, () => {
      for (const c of [t.success, t.warning, t.danger])
        expect(contrastRatio(c, t.bg)).toBeGreaterThanOrEqual(3)
    })
    it(`${mode}: every token value is present in main.css (TS and CSS stay in sync)`, () => {
      for (const value of Object.values(t)) expect(css).toContain(value.toLowerCase())
    })
  }
})
