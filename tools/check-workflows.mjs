// Verifies the rules in specs/ci.feature against every workflow file. Run: node tools/check-workflows.mjs
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const dir = join(import.meta.dirname, '..', '.github', 'workflows')
const failures = []
const files = readdirSync(dir).filter((f) => /\.ya?ml$/.test(f))
if (files.length === 0) failures.push('no workflow files found')

for (const f of files) {
  const text = readFileSync(join(dir, f), 'utf8')
  const lines = text.split('\n')
  lines.forEach((line, i) => {
    const m = line.match(/^\s*-?\s*uses:\s*(\S+)/)
    if (m && !m[1].startsWith('./') && !/@[0-9a-f]{40}$/.test(m[1]))
      failures.push(`${f}:${i + 1} action not pinned to a 40-char SHA: ${m[1]}`)
  })
  if (/pull_request_target/.test(text)) failures.push(`${f}: pull_request_target is not allowed`)
  if (!/^permissions:\s*\n\s+contents:\s*read\s*$/m.test(text))
    failures.push(`${f}: top-level permissions must be exactly contents: read`)
  const checkouts = lines.filter((l) => /uses:\s*actions\/checkout@/.test(l)).length
  const noPersist = (text.match(/persist-credentials:\s*false/g) ?? []).length
  if (checkouts !== noPersist) failures.push(`${f}: every checkout needs persist-credentials: false`)
}

if (failures.length) {
  console.error(failures.join('\n'))
  process.exit(1)
}
console.log(`ok: ${files.length} workflow file(s) satisfy specs/ci.feature`)
