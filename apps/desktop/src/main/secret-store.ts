import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from 'fs'
import { join } from 'path'

export type SafeStorageLike = {
  isEncryptionAvailable: () => boolean
  encryptString: (plain: string) => Buffer
  decryptString: (encrypted: Buffer) => string
}

export const isValidSecretName = (name: string): boolean => /^[a-z][a-z0-9_]{0,63}$/.test(name)

type Items = Record<string, string>

/**
 * API keys encrypted with the OS keystore (Windows DPAPI via Electron safeStorage).
 * If encryption is unavailable we refuse to store: there is deliberately NO plaintext fallback.
 */
export function createSecretStore({
  dir,
  safeStorage
}: {
  dir: string
  safeStorage: SafeStorageLike
}): {
  set: (name: string, value: string) => void
  delete: (name: string) => void
  names: () => string[]
  getAll: () => Record<string, string>
} {
  const file = join(dir, 'secrets.json')

  const load = (): Items => {
    try {
      if (!existsSync(file)) return {}
      const raw = JSON.parse(readFileSync(file, 'utf-8'))
      return raw && typeof raw.items === 'object' && raw.items ? (raw.items as Items) : {}
    } catch {
      return {}
    }
  }

  const save = (items: Items): void => {
    mkdirSync(dir, { recursive: true })
    const tmp = `${file}.tmp`
    writeFileSync(tmp, JSON.stringify({ version: 1, items }), { mode: 0o600 })
    renameSync(tmp, file)
  }

  return {
    set(name, value) {
      if (!isValidSecretName(name)) throw new Error('invalid secret name')
      if (typeof value !== 'string' || value.length === 0 || value.length > 4096)
        throw new Error('invalid secret value')
      if (!safeStorage.isEncryptionAvailable()) throw new Error('encryption-unavailable')
      const items = load()
      items[name] = safeStorage.encryptString(value).toString('base64')
      save(items)
    },
    delete(name) {
      if (!isValidSecretName(name)) throw new Error('invalid secret name')
      const items = load()
      delete items[name]
      save(items)
    },
    names: () => Object.keys(load()).sort(),
    getAll() {
      const out: Record<string, string> = {}
      for (const [name, enc] of Object.entries(load())) {
        try {
          out[name] = safeStorage.decryptString(Buffer.from(enc, 'base64'))
        } catch {
          /* undecryptable entry (e.g. other OS user): skip */
        }
      }
      return out
    }
  }
}
