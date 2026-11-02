import {
  PET_EVENTS,
  PET_MODES,
  petMessage,
  type PetContext,
  type PetEvent,
  type PetMode,
  type PetReaction
} from '@jarvis/shared'

/** The only thing that talks to OpenPets. Swapping or fixing the protocol touches one file. */
export type PetTransport = {
  react: (reaction: PetReaction) => Promise<unknown>
  say: (text: string) => Promise<unknown>
  status: () => Promise<{ available: boolean }>
}

export type PetStatus = { available: boolean; mode: PetMode }

const NUDGE_COOLDOWN_MS = 5 * 60_000
const REPEAT_WINDOW_MS = 30_000
const NUDGES: ReadonlySet<PetEvent> = new Set(['idle', 'distraction'])
// Celebrations may repeat (two level-ups in a row are both real); everything else is not repeated verbatim.
const REPEATABLE: ReadonlySet<PetEvent> = new Set(['gate_pass', 'level_up'])

const cleanContext = (ctx: unknown): PetContext => {
  const c = (ctx ?? {}) as Record<string, unknown>
  const out: PetContext = {}
  if (typeof c.retentionPct === 'number' && Number.isFinite(c.retentionPct))
    out.retentionPct = Math.max(0, Math.min(100, Math.round(c.retentionPct)))
  if (typeof c.level === 'number' && Number.isInteger(c.level) && c.level >= 1) out.level = c.level
  return out
}

export function createPetService({
  transport,
  now = Date.now
}: {
  transport: PetTransport
  now?: () => number
}): {
  event: (name: PetEvent, ctx?: PetContext) => Promise<boolean>
  setMode: (mode: PetMode) => void
  getMode: () => PetMode
  status: () => Promise<PetStatus>
  test: () => Promise<boolean>
} {
  let mode: PetMode = 'coach'
  let lastSendFailed = false
  const lastNudge = new Map<PetEvent, number>()
  let lastSaid: { text: string; at: number } | null = null

  const send = async (reaction: PetReaction, say?: string): Promise<boolean> => {
    try {
      await transport.react(reaction)
      if (say !== undefined) await transport.say(say)
      lastSendFailed = false
      return true
    } catch {
      lastSendFailed = true // OpenPets not running or it rejected the message: carry on silently
      return false
    }
  }

  return {
    async event(name, ctx) {
      if (!(PET_EVENTS as readonly string[]).includes(name)) return false
      const t = now()
      if (NUDGES.has(name)) {
        const last = lastNudge.get(name)
        if (last !== undefined && t - last < NUDGE_COOLDOWN_MS) return false
      }
      const msg = petMessage(name, mode, cleanContext(ctx))
      if (
        msg.say !== undefined &&
        !REPEATABLE.has(name) &&
        lastSaid &&
        lastSaid.text === msg.say &&
        t - lastSaid.at < REPEAT_WINDOW_MS
      )
        return false
      const ok = await send(msg.reaction, msg.say)
      if (ok) {
        if (NUDGES.has(name)) lastNudge.set(name, t)
        if (msg.say !== undefined) lastSaid = { text: msg.say, at: t }
      }
      return ok
    },
    setMode(next) {
      if ((PET_MODES as readonly string[]).includes(next)) mode = next
    },
    getMode: () => mode,
    async status() {
      if (lastSendFailed) return { available: false, mode }
      try {
        return { available: (await transport.status()).available, mode }
      } catch {
        return { available: false, mode }
      }
    },
    async test() {
      return send('waving', 'Hello! JARVIS aur pet ek saath taiyaar hain.')
    }
  }
}
