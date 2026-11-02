/** Focus Guard window classification: simple rules, applied in memory. Titles are never stored. */
export type FocusCategory = 'study' | 'neutral' | 'distraction'
export type WindowInfo = { app: string; title?: string; path?: string }

const norm = (s: string | undefined): string => (s ?? '').toLowerCase()

/** JARVIS itself and the pet window are not sampled at all. */
const SELF = /\b(openpets|upsc[ -]?jarvis|jarvis)\b/

// Start-of-word match only, so "SumatraPDF" and "AcroRd32" still match their stem.
const STUDY_APPS =
  /\b(acrobat|acrord32|sumatra|foxit|okular|evince|obsidian|anki|onenote|winword|notion|zotero|calibre)/
const DISTRACTION_APPS =
  /\b(steam|epicgames|epic games|valorant|leagueclient|minecraft|fortnite|netflix|primevideo|hotstar|bgmi|pubg|roblox)/
const BROWSERS = /\b(chrome|msedge|edge|firefox|brave|opera|vivaldi|safari)\b/

const STUDY_TITLE =
  /\b(upsc|ias|iasbaba|drishti|nptel|vision ias|insightsias|the hindu|indian express|pib|prs india|laxmikanth|ncert|khan academy|byju|unacademy|wikipedia)\b/
const DISTRACTION_TITLE =
  /\b(youtube|instagram|facebook|netflix|prime video|hotstar|reddit|twitter|tiktok|snapchat|9gag|disney|twitch|shorts|reels)\b/

/** Returns null for windows that must be ignored (JARVIS, OpenPets). */
export function classifyWindow(w: WindowInfo): FocusCategory | null {
  const app = norm(w.app)
  const path = norm(w.path)
  if (SELF.test(app) || SELF.test(path) || SELF.test(norm(w.title))) return null
  if (DISTRACTION_APPS.test(app)) return 'distraction'
  if (STUDY_APPS.test(app)) return 'study'
  if (BROWSERS.test(app) || BROWSERS.test(path)) {
    const title = norm(w.title)
    // Study keywords win: a study video on YouTube is not a distraction.
    if (STUDY_TITLE.test(title)) return 'study'
    if (DISTRACTION_TITLE.test(title)) return 'distraction'
  }
  return 'neutral'
}
