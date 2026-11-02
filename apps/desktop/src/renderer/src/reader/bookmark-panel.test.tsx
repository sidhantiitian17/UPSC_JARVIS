import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { BookmarkPanel } from './bookmark-panel'

const CHUNKS = [
  {
    id: 11,
    page: 5,
    ordinal: 0,
    text: 'First paragraph about federalism.',
    char_start: 0,
    char_end: 30
  },
  {
    id: 12,
    page: 5,
    ordinal: 1,
    text: 'Second paragraph about Article 3.',
    char_start: 31,
    char_end: 60
  }
]
const point = (chunk_id: number, page: number, ordinal: number): object => ({
  chunk_id,
  page,
  ordinal
})
const session = (over: object = {}): object => ({
  id: 3,
  document_id: 7,
  document_title: 'Polity',
  status: 'running',
  started_at: '2026-11-01T10:00:00Z',
  ended_at: null,
  focused_seconds: 0,
  start: point(11, 5, 0),
  end: null,
  tags: [],
  needs_tagging: false,
  source_budget: [],
  ...over
})
const TREE = [
  {
    id: 'gs3',
    parent_id: null,
    title: 'GS Paper III',
    kind: 'paper',
    paper: 'GS3',
    reviewed: false,
    source: 'draft',
    children: [
      {
        id: 'gs3.economy',
        parent_id: 'gs3',
        title: 'Indian Economy',
        kind: 'subject',
        paper: 'GS3',
        reviewed: false,
        source: 'draft',
        children: []
      }
    ]
  }
]

type Res = { status: number; body: unknown }
function setup(routes: Record<string, Res | ((body: unknown) => Res)>): ReturnType<typeof vi.fn> {
  const api = vi.fn(async (req: { method: string; path: string; body?: unknown }): Promise<Res> => {
    const r = routes[`${req.method} ${req.path}`]
    if (!r) return { status: 404, body: null }
    return typeof r === 'function' ? r(req.body) : r
  })
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true })
  }
  return api
}
const chunksRoute = { 'GET /library/documents/7/pages/5/chunks': { status: 200, body: CHUNKS } }

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('BookmarkPanel', () => {
  it('lists the chunks of the current page and sets a start bookmark', async () => {
    const api = setup({
      ...chunksRoute,
      'GET /sessions/active': { status: 200, body: null },
      'POST /sessions': { status: 200, body: session() }
    })
    render(<BookmarkPanel documentId={7} page={5} />)
    expect(await screen.findByText(/second paragraph about article 3/i)).toBeInTheDocument()
    await userEvent.click(
      screen.getByRole('button', { name: /set start bookmark at paragraph 2/i })
    )
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/sessions',
        body: { document_id: 7, start_chunk_id: 12 }
      })
    )
    expect(await screen.findByRole('status')).toHaveTextContent(
      /reading since page 5, paragraph 1/i
    )
  })

  it('offers end bookmarks while a session of this document is running, and not earlier than the start', async () => {
    setup({
      ...chunksRoute,
      'GET /sessions/active': { status: 200, body: session({ start: point(12, 5, 1) }) }
    })
    render(<BookmarkPanel documentId={7} page={5} />)
    await screen.findByRole('status')
    expect(screen.getByRole('button', { name: /set end bookmark at paragraph 1/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /set end bookmark at paragraph 2/i })).toBeEnabled()
    expect(screen.queryByRole('button', { name: /set start bookmark/i })).not.toBeInTheDocument()
  })

  it('ends the session and shows tags, the gate hint and a Source Budget warning', async () => {
    const done = session({
      status: 'gate',
      end: point(12, 5, 1),
      tags: [{ id: 'gs2.polity', title: 'Constitution and Polity' }],
      source_budget: [{ node_id: 'gs2.polity', title: 'Constitution and Polity', sources: 4 }]
    })
    const api = setup({
      ...chunksRoute,
      'GET /sessions/active': { status: 200, body: session() },
      'POST /sessions/3/end': { status: 200, body: done }
    })
    render(<BookmarkPanel documentId={7} page={5} />)
    await userEvent.click(
      await screen.findByRole('button', { name: /set end bookmark at paragraph 2/i })
    )
    expect(api).toHaveBeenCalledWith({
      method: 'POST',
      path: '/sessions/3/end',
      body: { end_chunk_id: 12 }
    })
    const result = await screen.findByRole('region', { name: /session saved/i })
    expect(within(result).getByText('Constitution and Polity')).toBeInTheDocument()
    expect(within(result).getByText(/4 sources/i)).toBeInTheDocument()
    expect(within(result).getByText(/recall gate/i)).toBeInTheDocument()
  })

  it('lets the owner tag manually when automatic tagging found nothing', async () => {
    const untagged = session({ status: 'gate', end: point(12, 5, 1), needs_tagging: true })
    const tagged = session({
      status: 'gate',
      end: point(12, 5, 1),
      tags: [{ id: 'gs3.economy', title: 'Indian Economy' }]
    })
    const api = setup({
      ...chunksRoute,
      'GET /sessions/active': { status: 200, body: session() },
      'POST /sessions/3/end': { status: 200, body: untagged },
      'GET /syllabus/tree': { status: 200, body: TREE },
      'PUT /sessions/3/tags': { status: 200, body: tagged }
    })
    render(<BookmarkPanel documentId={7} page={5} />)
    await userEvent.click(
      await screen.findByRole('button', { name: /set end bookmark at paragraph 2/i })
    )
    await userEvent.selectOptions(
      await screen.findByRole('combobox', { name: /syllabus node/i }),
      'gs3.economy'
    )
    await userEvent.click(screen.getByRole('button', { name: /save tag/i }))
    expect(api).toHaveBeenCalledWith({
      method: 'PUT',
      path: '/sessions/3/tags',
      body: { node_ids: ['gs3.economy'] }
    })
    expect(await screen.findByText('Indian Economy')).toBeInTheDocument()
  })

  it('cancels a running session', async () => {
    const api = setup({
      ...chunksRoute,
      'GET /sessions/active': { status: 200, body: session() },
      'POST /sessions/3/cancel': { status: 200, body: session({ status: 'skipped' }) }
    })
    render(<BookmarkPanel documentId={7} page={5} />)
    await userEvent.click(await screen.findByRole('button', { name: /cancel session/i }))
    expect(api).toHaveBeenCalledWith({
      method: 'POST',
      path: '/sessions/3/cancel',
      body: undefined
    })
    expect(
      await screen.findByRole('button', { name: /set start bookmark at paragraph 1/i })
    ).toBeInTheDocument()
  })

  it('shows the server message when a bookmark is refused', async () => {
    setup({
      ...chunksRoute,
      'GET /sessions/active': { status: 200, body: null },
      'POST /sessions': {
        status: 409,
        body: { detail: { message: 'A study session is already running.', session_id: 9 } }
      }
    })
    render(<BookmarkPanel documentId={7} page={5} />)
    await userEvent.click(
      await screen.findByRole('button', { name: /set start bookmark at paragraph 1/i })
    )
    expect(await screen.findByRole('alert')).toHaveTextContent(/already running/i)
  })

  it('explains when a page has no readable text', async () => {
    setup({
      'GET /library/documents/7/pages/5/chunks': { status: 200, body: [] },
      'GET /sessions/active': { status: 200, body: null }
    })
    render(<BookmarkPanel documentId={7} page={5} />)
    expect(await screen.findByText(/no readable text on this page/i)).toBeInTheDocument()
  })
})
