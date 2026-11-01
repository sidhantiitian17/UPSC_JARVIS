// Launches the BUILT app (run `pnpm build` first) and checks the shell + security basics.
// Linux CI/cloud: xvfb-run -a pnpm e2e      Windows/macOS: pnpm e2e
import { _electron as electron } from 'playwright-core'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
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
  check('preload bridge present', (await win.evaluate(() => typeof window.jarvis)) === 'object')
} catch (e) {
  console.error(e)
  failed = true
} finally {
  await app.close()
}
process.exit(failed ? 1 : 0)
