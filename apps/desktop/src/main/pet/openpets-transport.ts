import type { OpenPetsClient } from '@open-pets/client'
import type { PetTransport } from './pet-service'

/**
 * Real OpenPets transport (named-pipe IPC through @open-pets/client 4.1.0, pinned).
 * The client is loaded lazily so the app starts even when OpenPets is not installed.
 */
export function createOpenPetsTransport(): PetTransport {
  let client: OpenPetsClient | null = null
  const get = async (): Promise<OpenPetsClient> => {
    if (!client) {
      const mod = await import('@open-pets/client')
      client = mod.createOpenPetsClient({ connectTimeoutMs: 1500, responseTimeoutMs: 2500 })
    }
    return client
  }
  return {
    react: async (reaction) => (await get()).react(reaction),
    say: async (text) => (await get()).say(text),
    status: async () => {
      const s = await (await get()).status()
      return { available: s.ok && s.appRunning }
    }
  }
}
