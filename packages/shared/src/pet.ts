/** Pet events, modes and message rules. Pure data + functions, shared by the main process and tests. */
export const PET_EVENTS = [
  'session_start',
  'idle',
  'gate_pass',
  'gate_not_passed',
  'level_up',
  'distraction'
] as const
export type PetEvent = (typeof PET_EVENTS)[number]

export const PET_MODES = ['coach', 'strict', 'silent'] as const
export type PetMode = (typeof PET_MODES)[number]

/** Reactions accepted by OpenPets 4.1.0 (`celebrate` and `sleepy` are rejected by the app). */
export const PET_REACTIONS = [
  'idle',
  'thinking',
  'working',
  'editing',
  'running',
  'testing',
  'waiting',
  'waving',
  'success',
  'error',
  'celebrating'
] as const
export type PetReaction = (typeof PET_REACTIONS)[number]

export const PET_MAX_SAY = 140

/** Words the pet must never use (docs/04-UX-STRATEGY.md section 9: coach, not shame). */
export const SHAME_WORDS = [
  'lazy',
  'fail',
  'failure',
  'shame',
  'behind',
  'weak',
  'pathetic',
  'useless',
  'stupid',
  'waste',
  'nikamma',
  'bekaar'
] as const

export type PetContext = { retentionPct?: number; level?: number }
export type PetMessage = { reaction: PetReaction; say?: string }

const REACTION: Record<PetEvent, PetReaction> = {
  session_start: 'working',
  idle: 'waiting',
  gate_pass: 'celebrating',
  gate_not_passed: 'thinking',
  level_up: 'celebrating',
  distraction: 'waving'
}

type Template = (ctx: PetContext) => string

const COACH: Record<PetEvent, Template> = {
  session_start: () => 'Session shuru. Ek page ek baar, main yahin hoon.',
  idle: () => 'Thoda break? Paani pi lo, phir wapas aate hain.',
  gate_pass: (c) =>
    c.retentionPct !== undefined
      ? `Gate pass, ${c.retentionPct}% yaad. Shabaash.`
      : 'Gate pass! Jo padha, wo yaad bhi hai. Shabaash.',
  gate_not_passed: () =>
    'Is baar gate nahi nikla, koi baat nahi. Restudy list dekhte hain, phir dobara.',
  level_up: (c) =>
    c.level !== undefined
      ? `Level ${c.level}! Steady chal rahe ho.`
      : 'Level badh gaya! Steady chal rahe ho.',
  distraction: () => 'Wapas page par? Ek gehri saans, phir bas ek paragraph.'
}

const STRICT: Record<PetEvent, Template> = {
  session_start: () => 'Session shuru. Sirf padhai.',
  idle: () => 'Idle ho. Resume karo ya break lo.',
  gate_pass: (c) =>
    c.retentionPct !== undefined ? `Gate pass. Retention ${c.retentionPct}%.` : 'Gate pass.',
  gate_not_passed: () => 'Gate nahi nikla. Restudy list dekho.',
  level_up: (c) => (c.level !== undefined ? `Level ${c.level}.` : 'Level up.'),
  distraction: () => 'Focus block chal raha hai. Wapas padhai par.'
}

/** What the pet does for an event. Silent mode animates only; every text is capped at PET_MAX_SAY. */
export function petMessage(event: PetEvent, mode: PetMode, ctx: PetContext = {}): PetMessage {
  const reaction = REACTION[event]
  if (mode === 'silent') return { reaction }
  const text = (mode === 'strict' ? STRICT : COACH)[event](ctx)
  return {
    reaction,
    say: text.length > PET_MAX_SAY ? text.slice(0, PET_MAX_SAY - 1) + '…' : text
  }
}
