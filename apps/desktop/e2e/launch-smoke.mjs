/* eslint-disable @typescript-eslint/explicit-function-return-type -- plain JS script, no type annotations possible */
// Launches the BUILT app (run `pnpm build` first) and checks the shell + security basics.
// Linux CI/cloud: xvfb-run -a pnpm e2e      Windows/macOS: pnpm e2e
import { _electron as electron } from 'playwright-core'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { execSync } from 'node:child_process'
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

const app = await electron.launch({
  executablePath: electronPath,
  args: [root, ...(process.platform === 'linux' ? ['--no-sandbox'] : [])],
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
