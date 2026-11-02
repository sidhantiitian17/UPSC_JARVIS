import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LibraryScreen } from './library-screen'

const DOC = {
  id: 1,
  title: 'Laxmikanth Polity',
  path: 'C:\\books\\polity.pdf',
  page_count: 120,
  scanned: false,
  chunks: 340,
  last_page: 1
}

type Res = { status: number; body: unknown }

function setup(opts: { docs?: unknown[]; picked?: string | null; add?: Res; hits?: unknown[] }): {
  api: ReturnType<typeof vi.fn>
  pickPdf: ReturnType<typeof vi.fn>
} {
  let docs = opts.docs ?? []
  const api = vi.fn(async (req: { method: string; path: string; body?: unknown }): Promise<Res> => {
    if (req.method === 'GET' && req.path === '/library/documents')
      return { status: 200, body: docs }
    if (req.method === 'POST' && req.path === '/library/documents') {
      const res = opts.add ?? { status: 200, body: { ...DOC, duplicate: false, warning: null } }
      if (res.status === 200) docs = [...docs, res.body]
      return res
    }
    if (req.method === 'GET' && req.path.startsWith('/library/search'))
      return { status: 200, body: opts.hits ?? [] }
    return { status: 404, body: null }
  })
  const pickPdf = vi.fn(async () =>
    opts.picked === undefined ? 'C:\\books\\polity.pdf' : opts.picked
  )
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true }),
    pickPdf,
    pathForFile: () => 'C:\\dropped\\x.pdf'
  }
  return { api, pickPdf }
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('Library screen', () => {
  it('shows an empty state with exactly one primary action', async () => {
    setup({ docs: [] })
    render(<LibraryScreen />)
    expect(await screen.findByTestId('empty-state')).toBeInTheDocument()
    const primary = screen
      .getAllByRole('button')
      .filter((b) => b.getAttribute('data-variant') === 'primary')
    expect(primary).toHaveLength(1)
    expect(primary[0]).toHaveTextContent(/add pdf/i)
  })

  it('lists documents with page and chunk counts', async () => {
    setup({ docs: [DOC] })
    render(<LibraryScreen />)
    const list = await screen.findByRole('list', { name: /documents/i })
    expect(within(list).getByText('Laxmikanth Polity')).toBeInTheDocument()
    expect(within(list).getByText(/120 pages/)).toBeInTheDocument()
    expect(within(list).getByText(/340 chunks/)).toBeInTheDocument()
  })

  it('adds the picked PDF through the sidecar and refreshes the list', async () => {
    const { api, pickPdf } = setup({ docs: [] })
    render(<LibraryScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /add pdf/i }))
    expect(pickPdf).toHaveBeenCalled()
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/library/documents',
        body: { path: 'C:\\books\\polity.pdf' }
      })
    )
    expect(await screen.findByText('Laxmikanth Polity')).toBeInTheDocument()
  })

  it('does nothing when the picker is cancelled', async () => {
    const { api } = setup({ docs: [], picked: null })
    render(<LibraryScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /add pdf/i }))
    expect(api).not.toHaveBeenCalledWith(expect.objectContaining({ method: 'POST' }))
  })

  it('warns about scanned PDFs and says when a file was already in the library', async () => {
    setup({
      docs: [],
      add: {
        status: 200,
        body: {
          ...DOC,
          scanned: true,
          chunks: 0,
          duplicate: false,
          warning: 'This looks like a scanned PDF'
        }
      }
    })
    render(<LibraryScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /add pdf/i }))
    expect(await screen.findByRole('status')).toHaveTextContent(/scanned pdf/i)
    expect(screen.getByText('Scanned')).toBeInTheDocument()
  })

  it('shows the sidecar message when a file is refused', async () => {
    setup({ docs: [], add: { status: 422, body: { detail: 'Only PDF files can be added.' } } })
    render(<LibraryScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /add pdf/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Only PDF files can be added.')
  })

  it('searches the library and shows page and text of each hit', async () => {
    setup({
      docs: [DOC],
      hits: [
        {
          id: 5,
          document_id: 1,
          page: 42,
          char_start: 0,
          char_end: 30,
          text: 'Article 14 guarantees equality.'
        }
      ]
    })
    render(<LibraryScreen />)
    await userEvent.type(
      await screen.findByRole('searchbox', { name: /search library/i }),
      'equality{enter}'
    )
    const hit = await screen.findByText(/Article 14 guarantees equality/)
    expect(hit).toBeInTheDocument()
    expect(screen.getByText(/page 42/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Laxmikanth Polity/, { selector: '[data-testid="hit-doc"]' })
    ).toBeInTheDocument()
  })

  it('opens the reader for a document and returns to the list', async () => {
    setup({ docs: [DOC] })
    render(<LibraryScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /open laxmikanth polity/i }))
    await userEvent.click(await screen.findByRole('button', { name: /back to library/i }))
    expect(await screen.findByRole('list', { name: /documents/i })).toBeInTheDocument()
  })
})
