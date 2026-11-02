import type { PetContext, PetEvent } from '@jarvis/shared'

/** Fire-and-forget pet event. The pet is a nicety: it must never throw, block or show an error. */
export function petEvent(name: PetEvent, ctx?: PetContext): void {
  try {
    const result = window.jarvis?.pet?.event(name, ctx)
    void Promise.resolve(result).catch(() => undefined)
  } catch {
    /* no pet bridge (tests, or main not ready): ignore */
  }
}
