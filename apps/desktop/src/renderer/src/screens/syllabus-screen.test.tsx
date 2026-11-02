import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { SyllabusScreen } from './syllabus-screen'

type N = {
  id: string
  parent_id: string | null
  title: string
  kind: string
  paper: string | null
  reviewed: boolean
  source: string
  children: N[]
}
const n = (
  id: string,
  title: string,
  kind: string,
  children: N[] = [],
  over: Partial<N> = {}
): N => ({
  id,
  parent_id: null,
  title,
  kind,
  paper: null,
  reviewed: false,
  source: 'draft',
  children,
  ...over
})

const TREE: N[] = [
  n('gs2', 'GS Paper II', 'paper', [
    n(
      'gs2.polity',
      'Constitution and Polity',
      'subject',
      [n('gs2.polity.fr', 'Fundamental Rights', 'topic')],
      {
        reviewed: true,
        source: 'owner'
      }
    )
  ])
]

function mockApi(res: { status: number; body: unknown }, coverage: object[] = []): void {
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api: vi.fn(async (req: { path: string }) =>
      req.path === '/coverage/nodes' ? { status: 200, body: coverage } : res
    ),
    status: async () => ({ ready: true })
  }
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('Syllabus screen', () => {
  it('shows a tree with top levels open and deeper levels collapsed', async () => {
    mockApi({ status: 200, body: TREE })
    render(<SyllabusScreen />)
    const tree = await screen.findByRole('tree', { name: /syllabus/i })
    expect(within(tree).getByText('GS Paper II')).toBeInTheDocument()
    expect(within(tree).getByText('Constitution and Polity')).toBeInTheDocument()
    expect(within(tree).queryByText('Fundamental Rights')).not.toBeInTheDocument()
  })

  it('expands and collapses a node and exposes aria-expanded', async () => {
    mockApi({ status: 200, body: TREE })
    render(<SyllabusScreen />)
    const toggle = await screen.findByRole('button', { name: /expand constitution and polity/i })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    await userEvent.click(toggle)
    expect(screen.getByText('Fundamental Rights')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /collapse constitution and polity/i })
    ).toHaveAttribute('aria-expanded', 'true')
    await userEvent.click(screen.getByRole('button', { name: /collapse constitution and polity/i }))
    expect(screen.queryByText('Fundamental Rights')).not.toBeInTheDocument()
  })

  it('labels every node as draft or reviewed using text, not colour alone', async () => {
    mockApi({ status: 200, body: TREE })
    render(<SyllabusScreen />)
    await screen.findByRole('tree')
    expect(screen.getAllByText('Draft').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Reviewed')).toBeInTheDocument()
  })

  it('shows an empty state with a single primary action when there are no nodes', async () => {
    mockApi({ status: 200, body: [] })
    render(<SyllabusScreen />)
    expect(await screen.findByTestId('empty-state')).toBeInTheDocument()
    const primary = screen
      .getAllByRole('button')
      .filter((b) => b.getAttribute('data-variant') === 'primary')
    expect(primary).toHaveLength(1)
  })

  it('shows a friendly error when the sidecar fails', async () => {
    mockApi({ status: 500, body: null })
    render(<SyllabusScreen />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load the syllabus/i)
  })

  it('reload calls POST /syllabus/reload and shows validation errors', async () => {
    const api = vi.fn(async (req: { method: string; path: string }) => {
      if (req.path === '/syllabus/tree') return { status: 200, body: TREE }
      if (req.path === '/coverage/nodes') return { status: 200, body: [] }
      return { status: 422, body: { detail: 'a.yaml: invalid ontology (kind)' } }
    })
    ;(window as unknown as { jarvis: unknown }).jarvis = {
      platform: 'test',
      api,
      status: async () => ({ ready: true })
    }
    render(<SyllabusScreen />)
    await screen.findByRole('tree')
    await userEvent.click(screen.getByRole('button', { name: /reload syllabus files/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/syllabus/reload',
        body: undefined
      })
    )
    expect(await screen.findByRole('alert')).toHaveTextContent(/invalid ontology/)
  })

  it('shows verified progress per node: pages always, percent only when the target is known', async () => {
    const cov = (id: string, over: object): object => ({
      id,
      parent_id: null,
      title: id,
      kind: 'subject',
      verified_pages: 0,
      target_pages: null,
      percent: null,
      sessions: 0,
      ...over
    })
    mockApi({ status: 200, body: TREE }, [
      cov('gs2', { verified_pages: 12.5, target_pages: 50, percent: 25, sessions: 3 }),
      cov('gs2.polity', { verified_pages: 4, target_pages: null, percent: null, sessions: 1 })
    ])
    render(<SyllabusScreen />)
    await screen.findByRole('tree')
    const bar = await screen.findByRole('progressbar', { name: /GS Paper II verified/i })
    expect(bar).toHaveAttribute('aria-valuenow', '25')
    expect(screen.getByText('25% verified')).toBeInTheDocument()
    expect(screen.getByText(/12.5 pages verified/i)).toBeInTheDocument()
    expect(screen.getByText(/4 pages verified/i)).toBeInTheDocument()
    expect(screen.queryAllByRole('progressbar')).toHaveLength(1)
  })
})
