import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ReaderView } from './reader-view'
import { TimerContext, type TimerApi } from '../timer/timer-context'
import { IDLE } from '../timer/timer-machine'
import type { PdfEngine } from './pdf-engine'

const DOC = {
  id: 7,
  title: 'Polity',
  path: 'p.pdf',
  page_count: 10,
  scanned: false,
  chunks: 20,
  last_page: 4
}
const PDF_B64 = Buffer.from('%PDF-fake').toString('base64')

function fakeEngine(over: { open?: PdfEngine['open'] } = {}): {
  engine: PdfEngine
  renders: { page: number; scale: number }[]
} {
  const renders: { page: number; scale: number }[] = []
  const engine: PdfEngine = {
    open:
      over.open ??
      (async () => ({
        numPages: 10,
        destroy: vi.fn(),
        getPage: async (n: number) => ({
          baseWidth: 600,
          render: async (_c: HTMLCanvasElement, _t: HTMLElement, scale: number) => {
            renders.push({ page: n, scale })
          }
        })
      }))
  }
  return { engine, renders }
}

function setup(
  doc = DOC,
  fileRes: { status: number; body: unknown } | null = null
): {
  api: ReturnType<typeof vi.fn>
} {
  const api = vi.fn(async (req: { method: string; path: string; body?: unknown }) => {
    if (req.path === `/library/documents/${doc.id}`) return { status: 200, body: doc }
    if (req.path === `/library/documents/${doc.id}/file`)
      return fileRes ?? { status: 200, body: { contentType: 'application/pdf', base64: PDF_B64 } }
    if (req.path === '/sessions/active') return { status: 200, body: null }
    if (req.path.includes('/chunks')) return { status: 200, body: [] }
    if (req.method === 'PUT' && req.path.endsWith('/position'))
      return { status: 200, body: { ...doc, last_page: (req.body as { page: number }).page } }
    return { status: 404, body: null }
  })
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true })
  }
  return { api }
}

beforeEach(() => {
  vi.useRealTimers()
})
afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

const lastPage = (renders: { page: number }[]): number | undefined => renders.at(-1)?.page

describe('ReaderView', () => {
  it('opens on the last saved page and shows the position', async () => {
    setup()
    const { engine, renders } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    await waitFor(() => expect(lastPage(renders)).toBe(4))
    expect(screen.getByRole('spinbutton', { name: /page number/i })).toHaveValue(4)
    expect(screen.getByText(/of 10/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /polity/i })).toBeInTheDocument()
  })

  it('goes to next and previous pages and stops at the ends', async () => {
    setup({ ...DOC, last_page: 10 })
    const { engine, renders } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    await waitFor(() => expect(lastPage(renders)).toBe(10))
    expect(screen.getByRole('button', { name: /next page/i })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: /previous page/i }))
    await waitFor(() => expect(lastPage(renders)).toBe(9))
  })

  it('jumps to a typed page and clamps out-of-range input', async () => {
    setup()
    const { engine, renders } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    await waitFor(() => expect(lastPage(renders)).toBe(4))
    const input = screen.getByRole('spinbutton', { name: /page number/i })
    await userEvent.clear(input)
    await userEvent.type(input, '99{enter}')
    await waitFor(() => expect(lastPage(renders)).toBe(10))
  })

  it('supports keyboard navigation', async () => {
    setup()
    const { engine, renders } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    await waitFor(() => expect(lastPage(renders)).toBe(4))
    await userEvent.keyboard('{ArrowRight}')
    await waitFor(() => expect(lastPage(renders)).toBe(5))
    await userEvent.keyboard('{ArrowLeft}{ArrowLeft}')
    await waitFor(() => expect(lastPage(renders)).toBe(3))
  })

  it('zooms in and out within limits', async () => {
    setup()
    const { engine, renders } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    await waitFor(() => expect(renders.length).toBeGreaterThan(0))
    for (let i = 0; i < 20; i++)
      await userEvent.click(screen.getByRole('button', { name: /zoom in/i }))
    await waitFor(() => expect(renders.at(-1)?.scale).toBe(3))
    expect(screen.getByRole('button', { name: /zoom in/i })).toBeDisabled()
    for (let i = 0; i < 30; i++)
      await userEvent.click(screen.getByRole('button', { name: /zoom out/i }))
    await waitFor(() => expect(renders.at(-1)?.scale).toBe(0.5))
  })

  it('saves the reading position after the page changes', async () => {
    const { api } = setup()
    const { engine, renders } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    await waitFor(() => expect(lastPage(renders)).toBe(4))
    await userEvent.click(screen.getByRole('button', { name: /next page/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/library/documents/7/position',
        body: { page: 5 }
      })
    )
  })

  it('shows pages inverted in dark mode and lets the owner turn that off', async () => {
    setup()
    const { engine } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    const stage = await screen.findByTestId('page-stage')
    expect(stage).toHaveAttribute('data-invert', 'true')
    await userEvent.click(screen.getByRole('button', { name: /dark pages/i }))
    expect(stage).toHaveAttribute('data-invert', 'false')
  })

  it('shows a friendly error and a way back when the PDF cannot be opened', async () => {
    setup()
    const onBack = vi.fn()
    const { engine } = fakeEngine({
      open: async () => {
        throw new Error('Invalid PDF structure')
      }
    })
    render(<ReaderView documentId={7} engine={engine} onBack={onBack} />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not open/i)
    await userEvent.click(screen.getByRole('button', { name: /back to library/i }))
    expect(onBack).toHaveBeenCalled()
  })

  it('shows the sidecar message when the file has moved', async () => {
    setup(DOC, { status: 410, body: { detail: 'The PDF file has been moved or deleted.' } })
    const { engine } = fakeEngine()
    render(<ReaderView documentId={7} engine={engine} onBack={() => {}} />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/moved or deleted/i)
  })

  it('locks the page area when the focus timer expired during a session, keeping bookmarks usable', async () => {
    setup()
    const { engine } = fakeEngine()
    const expired: TimerApi = {
      state: { status: 'expired', kind: 'focus', totalMs: 3_000_000, focusedMs: 3_000_000 },
      clock: '00:00',
      focusedSeconds: 3000,
      minutes: { focus: 50, break: 10 },
      startFocus: () => {},
      startBreak: () => {},
      pause: () => {},
      resume: () => {},
      stop: () => {}
    }
    render(
      <TimerContext.Provider value={expired}>
        <ReaderView documentId={7} engine={engine} onBack={() => {}} />
      </TimerContext.Provider>
    )
    expect(await screen.findByRole('alertdialog', { name: /time is up/i })).toBeInTheDocument()
    expect(screen.getByText(/set your end bookmark/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next page/i })).toBeDisabled()
    expect(screen.getByRole('complementary', { name: /bookmarks/i })).toBeInTheDocument()
  })

  it('does not lock when the timer is idle', async () => {
    setup()
    const { engine, renders } = fakeEngine()
    const idle: TimerApi = {
      state: IDLE,
      clock: '50:00',
      focusedSeconds: 0,
      minutes: { focus: 50, break: 10 },
      startFocus: () => {},
      startBreak: () => {},
      pause: () => {},
      resume: () => {},
      stop: () => {}
    }
    render(
      <TimerContext.Provider value={idle}>
        <ReaderView documentId={7} engine={engine} onBack={() => {}} />
      </TimerContext.Provider>
    )
    await waitFor(() => expect(renders.length).toBeGreaterThan(0))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })
})
