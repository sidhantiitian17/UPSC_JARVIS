import { join } from 'path'

export type ChildLike = {
  kill: () => void
  once: (event: 'exit', cb: (code: number | null) => void) => void
}

export type SidecarDeps = {
  spawn: (
    cmd: string,
    args: string[],
    opts: { env: Record<string, string>; cwd?: string }
  ) => ChildLike
  findFreePort: () => Promise<number>
  makeToken: () => string
  fetchHealth: (baseUrl: string, token: string) => Promise<boolean>
  sleep: (ms: number) => Promise<void>
  now: () => number
}

export type SidecarConfig = {
  command: string
  args: (port: number) => string[]
  cwd?: string
  baseEnv?: Record<string, string>
  timeoutMs?: number
}

export type RunningSidecar = { baseUrl: string; token: string; stop: () => void }

const POLL_MS = 250

/** Starts the sidecar on a random loopback port with a per-launch token (passed by env, never argv). */
export async function startSidecar(cfg: SidecarConfig, deps: SidecarDeps): Promise<RunningSidecar> {
  const timeoutMs = cfg.timeoutMs ?? 30000
  const port = await deps.findFreePort()
  const token = deps.makeToken()
  const baseUrl = `http://127.0.0.1:${port}`
  const child = deps.spawn(cfg.command, cfg.args(port), {
    env: { ...(cfg.baseEnv ?? {}), JARVIS_TOKEN: token },
    cwd: cfg.cwd
  })
  let exited: number | null | undefined
  child.once('exit', (code) => {
    exited = code
  })

  const start = deps.now()
  for (;;) {
    if (exited !== undefined) throw new Error(`sidecar exited with code ${exited}`)
    if (await deps.fetchHealth(baseUrl, token)) break
    if (deps.now() - start >= timeoutMs) {
      child.kill()
      throw new Error(`sidecar did not become healthy within ${timeoutMs} ms`)
    }
    await deps.sleep(POLL_MS)
  }
  return { baseUrl, token, stop: () => child.kill() }
}

/** Dev default: `uv run --project apps/sidecar python -m jarvis`. Packaged builds set JARVIS_SIDECAR_BIN. */
export function resolveSidecarCommand(
  appDir: string,
  env: Record<string, string | undefined>
): Pick<SidecarConfig, 'command' | 'args'> {
  if (env.JARVIS_SIDECAR_BIN) {
    return { command: env.JARVIS_SIDECAR_BIN, args: (p) => ['--port', String(p)] }
  }
  const project = join(appDir, '..', 'sidecar')
  return {
    command: 'uv',
    args: (p) => ['run', '--project', project, 'python', '-m', 'jarvis', '--port', String(p)]
  }
}
