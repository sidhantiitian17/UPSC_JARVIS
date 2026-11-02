/* eslint-disable @typescript-eslint/explicit-function-return-type -- plain JS script, no type annotations possible */
// Launches the BUILT app (run `pnpm build` first) and checks the shell + security basics.
// Linux CI/cloud: xvfb-run -a pnpm e2e      Windows/macOS: pnpm e2e
import { _electron as electron } from 'playwright-core'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, readdirSync, writeFileSync } from 'node:fs'
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
  const vaultDir = path.join(userData, 'vault')
  mkdirSync(vaultDir)
  const vaultSet = await win.evaluate(
    (v) => window.jarvis.api({ method: 'PUT', path: '/settings', body: { vault_path: v } }),
    vaultDir
  )
  check('vault folder accepted', vaultSet.status === 200)
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
  const sessionNotes = readdirSync(path.join(vaultDir, 'JARVIS', 'Sessions')).filter((f) =>
    f.endsWith('.md')
  )
  const dailyNotes = readdirSync(path.join(vaultDir, 'JARVIS', 'Daily')).filter((f) =>
    f.endsWith('.md')
  )
  check(
    'Obsidian mirror wrote a session note and a daily note',
    sessionNotes.length === 1 && dailyNotes.length === 1
  )
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
  const levelShown = await win
    .waitForSelector('text=/Level \\d+/', { timeout: 10000 })
    .then(() => true)
    .catch(() => false)
  check('Today shows the level and streak card', levelShown)
  await win.click('button:has-text("Having a rough day?")')
  const badDayOn = await win
    .waitForSelector('text=/Bad-day mode is on for today/', { timeout: 10000 })
    .then(() => true)
    .catch(() => false)
  check('bad-day mode switches on from Today', badDayOn)
  await win.click('button:has-text("Back to the normal goal")')
  await win.fill('input[aria-label="Free hours"]', '3')
  await win.click('button:has-text("Make plan")')
  const planShown = await win
    .waitForSelector('ol[aria-label="Today\'s plan"] >> text=/min/', { timeout: 10000 })
    .then(() => true)
    .catch(() => false)
  check('Plan my day builds an hour-wise plan', planShown)
  await win.click('nav[aria-label="Main"] >> text=Insights')
  const insightsOk = await win
    .waitForSelector('section[aria-label="Claimed versus verified"]', { timeout: 10000 })
    .then(() => true)
    .catch(() => false)
  check('Insights shows claimed versus verified', insightsOk)
  await win.click('nav[aria-label="Main"] >> text=PYQ Lab')
  await win.waitForSelector('[data-testid="empty-state"]', { timeout: 10000 })
  await win.click('button:has-text("Import PYQs")')
  const pyqListed = await win
    .waitForSelector('li[aria-label="Prelims 2023 gs-paper-1"]', { timeout: 30000 })
    .then(() => true)
    .catch(() => false)
  check('PYQ Lab imports the real Phase 0 dataset and lists its papers', pyqListed)
  const pyqPapers = await win.evaluate(() =>
    window.jarvis.api({ method: 'GET', path: '/pyq/papers' })
  )
  check(
    'all 22 papers and 1587 questions are in SQLite',
    pyqPapers.status === 200 &&
      pyqPapers.body.length === 22 &&
      pyqPapers.body.reduce((n, p) => n + p.total, 0) === 1587
  )
  const tagged = await win.evaluate(async () => {
    const sug = await window.jarvis.api({
      method: 'POST',
      path: '/pyq/questions/PRE-2023-GS1-010/suggest-tags'
    })
    const q = await window.jarvis.api({ method: 'GET', path: '/pyq/questions/PRE-2023-GS1-010' })
    return { status: sug.status, tags: q.body.tags }
  })
  check(
    'PYQ tag suggestions run offline (keyword fallback) and stay suggestions until accepted',
    tagged.status === 200 && tagged.tags.every((t) => t.status === 'suggested'),
    JSON.stringify(tagged.tags.map((t) => t.source))
  )
  const petStatus = await win.evaluate(() => window.jarvis.pet.status())
  check(
    'pet bridge answers (OpenPets itself is optional)',
    typeof petStatus.available === 'boolean' && petStatus.mode === 'coach',
    JSON.stringify(petStatus)
  )
  const focusOff = await win.evaluate(() =>
    window.jarvis.api({ method: 'GET', path: '/focus/summary' })
  )
  check('Focus Guard is off by default', focusOff.status === 200 && focusOff.body.enabled === false)
  const refusedSamples = await win.evaluate(() =>
    window.jarvis.api({
      method: 'POST',
      path: '/focus/samples',
      body: { samples: [{ category: 'study', app: 'x' }] }
    })
  )
  check('samples are refused while Focus Guard is off', refusedSamples.status === 409)
  await win.evaluate(async () => {
    await window.jarvis.api({
      method: 'PUT',
      path: '/settings',
      body: { focus_guard_enabled: true }
    })
    await window.jarvis.focus.setEnabled(true)
  })
  const accepted = await win.evaluate(() =>
    window.jarvis.api({
      method: 'POST',
      path: '/focus/samples',
      body: { samples: [{ category: 'study', app: 'Acrobat' }] }
    })
  )
  check(
    'samples are accepted once the owner turns it on',
    accepted.status === 200 && accepted.body.stored === 1
  )
  await win.evaluate(async () => {
    await window.jarvis.api({
      method: 'PUT',
      path: '/settings',
      body: { focus_guard_enabled: false }
    })
    await window.jarvis.focus.setEnabled(false)
    await window.jarvis.api({ method: 'DELETE', path: '/privacy/focus?confirm=yes' })
  })
  const privacy = await win.evaluate(() =>
    window.jarvis.api({ method: 'GET', path: '/privacy/summary' })
  )
  check(
    'privacy summary lists stored data categories',
    privacy.status === 200 &&
      privacy.body.categories.length === 5 &&
      privacy.body.categories[1].count >= 1
  )
  await win.click('nav[aria-label="Main"] >> text=Today')
  const nextBlock = await win
    .waitForSelector('text=/e2e-polity, page/', { timeout: 10000 })
    .then(() => true)
    .catch(() => false)
  check('Today offers the next block from the last session', nextBlock)
  const cov = await win.evaluate(() =>
    window.jarvis.api({ method: 'GET', path: '/coverage/nodes' })
  )
  check('coverage endpoint serves every node', cov.status === 200 && cov.body.length > 0)
  const timerGone = await win.evaluate(() => document.querySelector('[role="timer"]') === null)
  check('timer stops when the session ends', timerGone)
  const sessionTags = await win.evaluate(async () => {
    const t = await window.jarvis.api({ method: 'GET', path: '/syllabus/tree' })
    return t.status
  })
  check('syllabus still served after session', sessionTags === 200)
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
