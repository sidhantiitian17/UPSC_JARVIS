import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { SidecarStatus } from './sidecar-status'

function setStatus(s: { ready: boolean; error?: string }): void {
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api: async () => ({ status: 200, body: {} }),
    status: async () => s
  }
}
afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('SidecarStatus', () => {
  it('shows an error banner with the reason when the engine failed to start', async () => {
    setStatus({ ready: false, error: 'uv not found' })
    render(<SidecarStatus pollMs={10} />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/uv not found/)
  })
  it('shows nothing when the engine is ready', async () => {
    setStatus({ ready: true })
    render(<SidecarStatus pollMs={10} />)
    await new Promise((r) => setTimeout(r, 40))
    expect(screen.queryByRole('alert')).toBeNull()
    expect(screen.queryByRole('status')).toBeNull()
  })
  it('shows a starting message while not ready and without error', async () => {
    setStatus({ ready: false })
    render(<SidecarStatus pollMs={10} />)
    expect(await screen.findByRole('status')).toHaveTextContent(/starting/i)
  })
})
