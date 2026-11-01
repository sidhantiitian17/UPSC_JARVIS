// @vitest-environment node
import { describe, expect, it, vi } from 'vitest'
import { killProcessTree } from './process-tree'

describe('killProcessTree', () => {
  it('on POSIX signals the whole process group (negative pid)', () => {
    const kill = vi.fn()
    killProcessTree(4242, 'linux', { kill, run: vi.fn() })
    expect(kill).toHaveBeenCalledWith(-4242, 'SIGTERM')
  })

  it('on Windows runs taskkill with /T (tree) and /F', () => {
    const run = vi.fn()
    killProcessTree(4242, 'win32', { kill: vi.fn(), run })
    expect(run).toHaveBeenCalledWith('taskkill', ['/pid', '4242', '/T', '/F'])
  })

  it('ignores an already-dead process and never throws', () => {
    const kill = vi.fn(() => {
      throw Object.assign(new Error('gone'), { code: 'ESRCH' })
    })
    expect(() => killProcessTree(1, 'darwin', { kill, run: vi.fn() })).not.toThrow()
  })

  it('does nothing for an invalid pid', () => {
    const kill = vi.fn()
    killProcessTree(0, 'linux', { kill, run: vi.fn() })
    killProcessTree(Number.NaN, 'linux', { kill, run: vi.fn() })
    expect(kill).not.toHaveBeenCalled()
  })
})
