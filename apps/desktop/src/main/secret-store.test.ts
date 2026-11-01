// @vitest-environment node
import { mkdtempSync, readFileSync, existsSync, writeFileSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { describe, expect, it } from 'vitest'
import { createSecretStore, isValidSecretName, type SafeStorageLike } from './secret-store'

// Fake OS keystore: "encrypts" by reversing and prefixing, so plaintext can never appear in the file.
function fakeSafeStorage(available = true): SafeStorageLike {
  return {
    isEncryptionAvailable: () => available,
    encryptString: (s) => Buffer.from('ENC:' + [...s].reverse().join('')),
    decryptString: (b) => [...b.toString().slice(4)].reverse().join('')
  }
}

const newDir = (): string => mkdtempSync(join(tmpdir(), 'jarvis-secrets-'))

describe('secret store (Electron safeStorage; never plaintext)', () => {
  it('round-trips values and lists names', () => {
    const dir = newDir()
    const s = createSecretStore({ dir, safeStorage: fakeSafeStorage() })
    s.set('gemini_key', 'AIza-SECRET-1')
    s.set('omniroute_key', 'or-SECRET-2')
    expect(s.names()).toEqual(['gemini_key', 'omniroute_key'])
    expect(s.getAll()).toEqual({ gemini_key: 'AIza-SECRET-1', omniroute_key: 'or-SECRET-2' })
  })

  it('never writes the plaintext to disk', () => {
    const dir = newDir()
    createSecretStore({ dir, safeStorage: fakeSafeStorage() }).set('gemini_key', 'AIza-SECRET-1')
    const raw = readFileSync(join(dir, 'secrets.json'), 'utf-8')
    expect(raw).not.toContain('AIza-SECRET-1')
    expect(raw).not.toContain('1-TERCES-azIA')
  })

  it('persists across instances and supports delete', () => {
    const dir = newDir()
    createSecretStore({ dir, safeStorage: fakeSafeStorage() }).set('gemini_key', 'v')
    const again = createSecretStore({ dir, safeStorage: fakeSafeStorage() })
    expect(again.getAll()).toEqual({ gemini_key: 'v' })
    again.delete('gemini_key')
    expect(createSecretStore({ dir, safeStorage: fakeSafeStorage() }).names()).toEqual([])
  })

  it('refuses to store anything when OS encryption is unavailable (no plaintext fallback)', () => {
    const dir = newDir()
    const s = createSecretStore({ dir, safeStorage: fakeSafeStorage(false) })
    expect(() => s.set('gemini_key', 'v')).toThrow(/encryption-unavailable/)
    expect(existsSync(join(dir, 'secrets.json'))).toBe(false)
  })

  it('validates names and values', () => {
    expect(isValidSecretName('gemini_key')).toBe(true)
    for (const bad of ['', 'Gemini', '../x', 'a b', 'x'.repeat(65)])
      expect(isValidSecretName(bad)).toBe(false)
    const s = createSecretStore({ dir: newDir(), safeStorage: fakeSafeStorage() })
    expect(() => s.set('Bad Name', 'v')).toThrow(/invalid secret name/)
    expect(() => s.set('gemini_key', '')).toThrow(/invalid secret value/)
    expect(() => s.set('gemini_key', 'x'.repeat(4097))).toThrow(/invalid secret value/)
  })

  it('treats a corrupt file as empty instead of crashing', () => {
    const dir = newDir()
    createSecretStore({ dir, safeStorage: fakeSafeStorage() }).set('gemini_key', 'v')
    writeFileSync(join(dir, 'secrets.json'), '{not json')
    expect(createSecretStore({ dir, safeStorage: fakeSafeStorage() }).names()).toEqual([])
  })
})
