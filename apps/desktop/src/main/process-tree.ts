export type KillDeps = {
  kill: (pid: number, signal: NodeJS.Signals) => void
  run: (cmd: string, args: string[]) => void
}

/**
 * Stops a spawned process AND its children (`uv run` starts python as a child, so killing only the
 * wrapper would leak the sidecar). POSIX: signal the process group (spawn with detached: true);
 * Windows: taskkill /T /F. Never throws: the process may already be gone.
 */
export function killProcessTree(
  pid: number | undefined,
  platform: NodeJS.Platform,
  deps: KillDeps
): void {
  if (!pid || !Number.isInteger(pid) || pid <= 0) return
  try {
    if (platform === 'win32') deps.run('taskkill', ['/pid', String(pid), '/T', '/F'])
    else deps.kill(-pid, 'SIGTERM')
  } catch {
    /* already exited */
  }
}
