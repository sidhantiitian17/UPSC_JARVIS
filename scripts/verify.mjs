// Cross-platform verification: lint + typecheck + tests for every part of the repo.
// Usage: pnpm verify   (add --only <name> to run one step)
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const win = process.platform === 'win32'

export const steps = [
  { name: 'js-lint', cmd: 'pnpm', args: ['lint'], cwd: root },
  { name: 'js-typecheck', cmd: 'pnpm', args: ['typecheck'], cwd: root },
  { name: 'js-test', cmd: 'pnpm', args: ['test'], cwd: root },
  { name: 'sidecar-lint', cmd: 'uv', args: ['run', 'ruff', 'check', '.'], cwd: path.join(root, 'apps/sidecar') },
  { name: 'sidecar-test', cmd: 'uv', args: ['run', 'pytest', '-q'], cwd: path.join(root, 'apps/sidecar') },
  { name: 'pyq-test', cmd: 'uv', args: ['run', 'pytest', '-q'], cwd: path.join(root, 'tools/pyq') },
  { name: 'brain-test', cmd: 'uv', args: ['run', 'pytest', '-q'], cwd: path.join(root, 'tools/brain') }
]

export function run(selected = steps) {
  const results = []
  for (const s of selected) {
    console.log(`\n=== ${s.name}: ${s.cmd} ${s.args.join(' ')}  (cwd ${path.relative(root, s.cwd) || '.'})`)
    const r = spawnSync(s.cmd, s.args, { cwd: s.cwd, stdio: 'inherit', shell: win })
    results.push({ name: s.name, ok: r.status === 0 })
    if (r.status !== 0) break
  }
  console.log('\n=== verify summary')
  for (const r of results) console.log(`${r.ok ? 'PASS' : 'FAIL'}  ${r.name}`)
  return results.length === selected.length && results.every((r) => r.ok)
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const only = process.argv.includes('--only') ? process.argv[process.argv.indexOf('--only') + 1] : null
  const selected = only ? steps.filter((s) => s.name === only) : steps
  process.exit(run(selected) ? 0 : 1)
}
