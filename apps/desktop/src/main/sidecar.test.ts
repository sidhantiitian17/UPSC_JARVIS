// @vitest-environment node
import { describe, expect, it, vi } from 'vitest'
import { resolveSidecarCommand, startSidecar, type ChildLike, type SidecarDeps } from './sidecar'

function fakeChild(): ChildLike & { killed: boolean; exit: (code: number | null) => void } {
  let onExit: ((c: number | null) => void) | undefined
  return {
    killed: false,
    kill() {
      this.killed = true
    },
    once(_ev, cb) {
      onExit = cb
    },
    exit(code) {
      onExit?.(code)
    }
  }
}

function deps(over: Partial<SidecarDeps> = {}): {
  d: SidecarDeps
  child: ReturnType<typeof fakeChild>
  spawn: ReturnType<typeof vi.fn>
} {
  const child = fakeChild()
  const spawn = vi.fn(() => child)
  let t = 0
  const d: SidecarDeps = {
    spawn,
    findFreePort: async () => 40123,
    makeToken: () => 'f'.repeat(64),
    fetchHealth: async () => true,
    sleep: async (ms) => {
      t += ms
    },
    now: () => t,
    ...over
  }
  return { d, child, spawn }
}

const cfg = {
  command: 'uv',
  args: (p: number) => ['run', 'python', '-m', 'jarvis', '--port', String(p)]
}

describe('startSidecar', () => {
  it('starts on a loopback URL with the token passed by environment, never argv', async () => {
    const { d, spawn } = deps()
    const s = await startSidecar(cfg, d)
    expect(s.baseUrl).toBe('http://127.0.0.1:40123')
    expect(s.token).toHaveLength(64)
    const [cmd, args, opts] = spawn.mock.calls[0] as unknown as [
      string,
      string[],
      { env: Record<string, string> }
    ]
    expect(cmd).toBe('uv')
    expect(args.join(' ')).not.toContain(s.token)
    expect(opts.env.JARVIS_TOKEN).toBe(s.token)
  })

  it('waits for health with retries before resolving', async () => {
    let calls = 0
    const { d } = deps({ fetchHealth: async () => ++calls >= 4 })
    await startSidecar(cfg, d)
    expect(calls).toBe(4)
  })

  it('kills the child and rejects when health never succeeds', async () => {
    const { d, child } = deps({ fetchHealth: async () => false })
    await expect(startSidecar({ ...cfg, timeoutMs: 1000 }, d)).rejects.toThrow(
      /did not become healthy/
    )
    expect(child.killed).toBe(true)
  })

  it('rejects immediately when the child exits early', async () => {
    const { d, child } = deps({
      fetchHealth: async () => {
        child.exit(3)
        return false
      }
    })
    await expect(startSidecar(cfg, d)).rejects.toThrow(/exited with code 3/)
  })

  it('stop() kills the child', async () => {
    const { d, child } = deps()
    const s = await startSidecar(cfg, d)
    s.stop()
    expect(child.killed).toBe(true)
  })
})

describe('resolveSidecarCommand', () => {
  it('uses uv with the sidecar project directory and no secrets in arguments', () => {
    const c = resolveSidecarCommand('/repo/apps/desktop', {})
    expect(c.command).toBe('uv')
    const args = c.args(5555)
    expect(args).toContain('--port')
    expect(args).toContain('5555')
    expect(args.join(' ')).toMatch(/apps[\\/]sidecar/)
  })

  it('allows an explicit override for packaged builds', () => {
    const c = resolveSidecarCommand('/x', { JARVIS_SIDECAR_BIN: '/opt/jarvis-sidecar' })
    expect(c.command).toBe('/opt/jarvis-sidecar')
    expect(c.args(7)).toEqual(['--port', '7'])
  })
})
