/* eslint-disable @typescript-eslint/explicit-function-return-type -- plain JS script, no type annotations possible */
// Launches the BUILT app (run `pnpm build` first) and checks the shell + security basics.
// Linux CI/cloud: xvfb-run -a pnpm e2e      Windows/macOS: pnpm e2e
import { _electron as electron } from 'playwright-core'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { createRequire } from 'node:module'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const electronPath = createRequire(import.meta.url)('electron')
const SCREENS = [
  'today',
  'study',
  'syllabus',
  'pyq',
  'mains',
  'ca',
  'interview',
  'browser',
  'insights',
  'settings'
]

// Throwaway profile so every run starts with an empty database and never touches the owner's data.
const userData = mkdtempSync(path.join(tmpdir(), 'jarvis-e2e-'))

/** Minimal one-page text PDF (no dependencies) so the real library pipeline can be exercised. */
function tinyPdf(lines) {
  const body = `BT /F1 12 Tf 14 TL 50 740 Td ${lines.map((l) => `(${l}) Tj T*`).join(' ')} ET`
  const objs = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    '<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
    '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
    `<< /Length ${body.length} >>\nstream\n${body}\nendstream`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>'
  ]
  let out = '%PDF-1.4\n'
  const offs = []
  objs.forEach((o, i) => {
    offs.push(out.length)
    out += `${i + 1} 0 obj\n${o}\nendobj\n`
  })
  const x = out.length
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n${offs.map((o) => `${String(o).padStart(10, '0')} 00000 n \n`).join('')}`
  out += `trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${x}\n%%EOF\n`
  return out
}

const app = await electron.launch({
  executablePath: electronPath,
  args: [
    root,
    `--user-data-dir=${userData}`,
    ...(process.platform === 'linux' ? ['--no-sandbox'] : [])
  ],
  cwd: root
})
let failed = false
const check = (name, ok, detail = '') => {
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? ` (${detail})` : ''}`)
  if (!ok) failed = true
}
try {
  const win = await app.firstWindow()
  await win.waitForSelector('nav[aria-label="Main"]', { timeout: 20000 })
  check('window title', (await win.title()) === 'UPSC JARVIS')
  const hrefs = await win.$$eval('nav[aria-label="Main"] a', (as) =>
    as.map((a) => a.getAttribute('href'))
  )
  check('ten sidebar links', JSON.stringify(hrefs) === JSON.stringify(SCREENS.map((s) => `#/${s}`)))
  await win.click('text=Syllabus')
  check('navigation works', (await win.textContent('h1')) === 'Syllabus')
  const treeOk = await win
    .waitForSelector('[role="tree"] >> text=GS Paper I', { timeout: 20000 })
    .then(() => true)
    .catch(() => false)
  check('syllabus tree loads from the real sidecar', treeOk)
  const leak = await win.evaluate(() => ({ req: typeof require, proc: typeof process }))
  check(
    'renderer has no node globals',
    leak.req === 'undefined' && leak.proc === 'undefined',
    JSON.stringify(leak)
  )
  // Real sidecar: engine becomes ready, /health works through the bridge, unsafe paths are refused.
  let ready = false
  for (let i = 0; i < 120 && !ready; i++) {
    ready = (await win.evaluate(() => window.jarvis.status())).ready
    if (!ready) await new Promise((r) => setTimeout(r, 500))
  }
  check('sidecar ready', ready)
  const health = await win.evaluate(() => window.jarvis.api({ method: 'GET', path: '/health' }))
  check(
    'GET /health through bridge',
    health.status === 200 && health.body.status === 'ok',
    JSON.stringify(health)
  )
  const refused = await win.evaluate(() =>
    window.jarvis.api({ method: 'GET', path: '/../etc/passwd' }).then(
      () => false,
      () => true
    )
  )
  check('unsafe api path refused', refused)

  // Real library pipeline through the bridge: add a PDF, see it listed, find it by search.
  const pdfPath = path.join(userData, 'e2e-polity.pdf')
  writeFileSync(
    pdfPath,
    tinyPdf([
      'Article 14 of the Constitution guarantees equality before law to all persons.',
      'The Lok Sabha has a maximum strength of 552 members elected by adults.',
      'The Rajya Sabha is a permanent house whose members retire every second year.',
      'The President appoints the Governor of each State for a term of five years.',
      'The Election Commission supervises elections to Parliament and State Legislatures.',
      'The Supreme Court can issue writs under Article 32 for Fundamental Rights.',
      'The Finance Commission is constituted every fifth year under Article 280.'
    ])
  )
  const added = await win.evaluate(
    (p) => window.jarvis.api({ method: 'POST', path: '/library/documents', body: { path: p } }),
    pdfPath
  )
  check(
    'PDF added to library',
    added.status === 200 && added.body.page_count === 1,
    JSON.stringify(added.body)
  )
  const found = await win.evaluate(() =>
    window.jarvis.api({ method: 'GET', path: '/library/search?q=equality' })
  )
  check('library search finds the text', found.status === 200 && found.body.length > 0)
  await win.click('text=Study')
  const listed = await win
    .waitForSelector('ul[aria-label="Documents"] >> text=e2e-polity', { timeout: 20000 })
    .then(() => true)
    .catch(() => false)
  check('Study screen lists the document', listed)
  await win.click('button[aria-label="Open e2e-polity"]')
  const textOk = await win
    .waitForFunction(
      () => document.querySelector('.textLayer')?.textContent?.includes('equality'),
      null,
      {
        timeout: 30000
      }
    )
    .then(() => true)
    .catch(() => false)
  check('reader renders the page with a text layer (pdf.js + worker)', textOk)
  const painted = await win.evaluate(() => {
    const c = document.querySelector('canvas')
    if (!c || c.width === 0) return false
    const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data
    for (let i = 3; i < d.length; i += 4) if (d[i] !== 0) return true
    return false
  })
  check('reader canvas has painted pixels', painted)
  await win.click('button[aria-label="Set start bookmark at paragraph 1"]')
  await win.waitForSelector('[role="status"] >> text=Reading since page 1')
  const timerShown = await win
    .waitForSelector('[role="timer"] >> text=Focus', { timeout: 10000 })
    .then(() => true)
    .catch(() => false)
  check('focus timer starts with the start bookmark', timerShown)
  const idle = await win.evaluate(() => window.jarvis.idleSeconds())
  check(
    'system idle time is readable from main',
    typeof idle === 'number' && idle >= 0,
    String(idle)
  )
  await win.click('button[aria-label="Set end bookmark at paragraph 1"]')
  const saved = await win
    .waitForSelector('section[aria-label="Session saved"]', { timeout: 30000 })
    .then(() => true)
    .catch(() => false)
  check('start/end bookmarks save a session', saved)
  // The recall gate opens by itself; answer every question by keyboard (offline cloze quiz: no AI keys here).
  const gateOpen = await win
    .waitForSelector('[role="dialog"][aria-label="Recall gate"] >> text=/Question 1 of/', {
      timeout: 30000
    })
    .then(() => true)
    .catch(() => false)
  check('recall gate opens after the end bookmark', gateOpen)
  const total = Number((await win.textContent('text=/Question 1 of/')).match(/of (\d+)/)[1])
  check('gate has questions from the range', total >= 3, String(total))
  for (let i = 0; i < total; i++) {
    await win.waitForSelector(`text=/Question ${i + 1} of/`)
    await win.keyboard.press('1')
    await win.keyboard.press('g')
    await win.waitForSelector('[data-testid="verdict"]')
    await win.keyboard.press('Enter')
  }
  const resultShown = await win
    .waitForSelector('section[aria-label="Gate result"]', { timeout: 15000 })
    .then(() => true)
    .catch(() => false)
  check('gate result is shown after the last answer', resultShown)
  const noGateWaiting = await win.evaluate(async () => {
    const r = await window.jarvis.api({ method: 'GET', path: '/sessions/awaiting-gate' })
    return r.status === 200 && r.body === null
  })
  check('finished gate no longer awaits', noGateWaiting)
  await win.click('button:has-text("Done")')
  const stats = await win.evaluate(() =>
    window.jarvis.api({ method: 'GET', path: '/review/stats' })
  )
  check(
    'wrong gate answers became FSRS cards',
    stats.status === 200 && stats.body.total_cards >= 1,
    JSON.stringify(stats.body)
  )
  await win.click('nav[aria-label="Main"] >> text=Today')
  const todayOk = await win
    .waitForSelector('h1:has-text("Today")', { timeout: 10000 })
    .then(() => true)
    .catch(() => false)
  check('Today screen renders with review stats', todayOk)
  const timerGone = await win.evaluate(() => document.querySelector('[role="timer"]') === null)
  check('timer stops when the session ends', timerGone)
  const sessionTags = await win.evaluate(async () => {
    const t = await window.jarvis.api({ method: 'GET', path: '/syllabus/tree' })
    return t.status
  })
  check('syllabus still served after session', sessionTags === 200)
  await win.click('text=Back to library')
  await win.click('text=Syllabus')
  const banner = await win.locator('[role=alert]').count()
  check('no error banner', banner === 0)
  check('preload bridge present', (await win.evaluate(() => typeof window.jarvis)) === 'object')
} catch (e) {
  console.error(e)
  failed = true
} finally {
  await app.close()
}
if (process.platform !== 'win32') {
  await new Promise((r) => setTimeout(r, 1500))
  // '[j]arvis' keeps pgrep from matching its own shell command line.
  const left = (() => {
    try {
      return execSync("pgrep -f '[j]arvis --port' || true").toString().trim()
    } catch {
      return ''
    }
  })()
  check('sidecar stopped with the app', left === '', left)
}
process.exit(failed ? 1 : 0)
