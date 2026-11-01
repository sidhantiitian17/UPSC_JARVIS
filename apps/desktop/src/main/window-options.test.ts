// @vitest-environment node
import { readFileSync } from 'fs'
import { resolve } from 'path'
import { describe, expect, it } from 'vitest'
import { isAllowedExternalUrl, secureWebPreferences } from './window-options'

describe('window security (CLAUDE.md agent rules)', () => {
  it('keeps contextIsolation and sandbox on and nodeIntegration off', () => {
    const p = secureWebPreferences('/app/preload.js')
    expect(p).toMatchObject({
      contextIsolation: true,
      sandbox: true,
      nodeIntegration: false,
      webSecurity: true
    })
    expect(p.preload).toBe('/app/preload.js')
  })

  it('only https URLs may be opened externally', () => {
    expect(isAllowedExternalUrl('https://example.com/a')).toBe(true)
    for (const bad of [
      'http://example.com',
      'file:///etc/passwd',
      'javascript:alert(1)',
      'not a url',
      ''
    ])
      expect(isAllowedExternalUrl(bad)).toBe(false)
  })

  it('the main entry uses the secure helper and never disables the sandbox', () => {
    const src = readFileSync(resolve(__dirname, 'index.ts'), 'utf-8')
    expect(src).toContain('secureWebPreferences')
    expect(src).not.toMatch(/sandbox:\s*false/)
    expect(src).not.toMatch(/nodeIntegration:\s*true/)
  })

  it('the preload script does not pull in node-only helpers', () => {
    const src = readFileSync(resolve(__dirname, '../preload/index.ts'), 'utf-8')
    expect(src).not.toContain('@electron-toolkit/preload')
  })
})
