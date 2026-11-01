import { spawn, spawnSync } from 'child_process'
import { randomBytes } from 'crypto'
import { createServer } from 'net'
import { killProcessTree } from './process-tree'
import type { SidecarDeps } from './sidecar'

/** Real implementations of the sidecar launcher's dependencies (thin glue, covered by `pnpm e2e`). */
export function realSidecarDeps(): SidecarDeps {
  return {
    spawn: (cmd, args, opts) => {
      const child = spawn(cmd, args, {
        env: { ...process.env, ...opts.env },
        cwd: opts.cwd,
        stdio: 'ignore',
        windowsHide: true,
        shell: false,
        detached: process.platform !== 'win32' // own process group so the whole tree can be stopped
      })
      return {
        once: (event, cb) => {
          child.once(event, cb)
        },
        kill: () =>
          killProcessTree(child.pid, process.platform, {
            kill: (pid, sig) => process.kill(pid, sig),
            run: (c, a) => {
              spawnSync(c, a, { stdio: 'ignore', windowsHide: true })
            }
          })
      }
    },
    findFreePort: () =>
      new Promise((resolve, reject) => {
        const srv = createServer()
        srv.once('error', reject)
        srv.listen(0, '127.0.0.1', () => {
          const addr = srv.address()
          const port = typeof addr === 'object' && addr ? addr.port : 0
          srv.close(() => resolve(port))
        })
      }),
    makeToken: () => randomBytes(32).toString('hex'),
    fetchHealth: async (baseUrl, token) => {
      try {
        const r = await fetch(`${baseUrl}/health`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: AbortSignal.timeout(1000)
        })
        return r.ok
      } catch {
        return false
      }
    },
    sleep: (ms) => new Promise((r) => setTimeout(r, ms)),
    now: () => Date.now()
  }
}
