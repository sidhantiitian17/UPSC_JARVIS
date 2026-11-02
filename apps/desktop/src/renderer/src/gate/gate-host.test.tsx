import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { GateProvider, useGate } from './gate-host'

const SESSION = { id: 3, document_id: 7, document_title: 'Polity', status: 'gate' }
const GATE = {
  session_id: 3,
  questions: [
    {
      id: 1,
      stem: 'Only question?',
      options: ['a', 'b', 'c', 'd'],
      style: 'recall',
      source: 'generated',
      interleaved: false,
      chunk_id: 1,
      page: 1,
      ordinal: 0
    }
  ],
  discarded: 0,
  fallback_used: false,
  short_range: false
}
const FAIL = {
  session_id: 3,
  total: 1,
  correct: 0,
  retention_pct: 0,
  passed: false,
  skipped: false,
  xp: 0,
  pass_mark: 70,
  restudy: [{ chunk_id: 1, book: 'Polity', page: 12, ordinal: 0, quote: 'q' }],
  nodes: []
}

function Probe(): React.JSX.Element {
  const { openGate, readerRequest } = useGate()
  const loc = useLocation()
  return (
    <div>
      <output aria-label="path">{loc.pathname}</output>
      <output aria-label="request">
        {readerRequest ? `${readerRequest.documentId}:${readerRequest.page}` : ''}
      </output>
      <button onClick={() => openGate({ sessionId: 3, documentId: 7 })}>open gate</button>
    </div>
  )
}

function setup(awaiting: object | null): void {
  const api = vi.fn(async (req: { method: string; path: string }) => {
    if (req.path === '/sessions/awaiting-gate') return { status: 200, body: awaiting }
    if (req.path === '/sessions/3/gate' && req.method === 'POST') return { status: 200, body: GATE }
    if (req.path === '/sessions/3/gate/answer')
      return {
        status: 200,
        body: {
          question_id: 1,
          correct: false,
          chosen_index: 0,
          answer_index: 1,
          explanation: '',
          source_quote: 'q',
          chunk_id: 1,
          page: 12,
          ordinal: 0
        }
      }
    if (req.path === '/sessions/3/gate/finish') return { status: 200, body: FAIL }
    return { status: 404, body: null }
  })
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true })
  }
}

const mount = (): void => {
  render(
    <MemoryRouter initialEntries={['/today']}>
      <GateProvider>
        <Probe />
      </GateProvider>
    </MemoryRouter>
  )
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('GateProvider', () => {
  it('reopens a gate that was waiting when the app started', async () => {
    setup(SESSION)
    mount()
    expect(await screen.findByRole('dialog', { name: /recall gate/i })).toBeInTheDocument()
  })

  it('shows nothing when no gate is waiting', async () => {
    setup(null)
    mount()
    await waitFor(() => expect(screen.getByLabelText('path')).toBeInTheDocument())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('opens a gate on request and hides it when closed', async () => {
    setup(null)
    mount()
    await userEvent.click(screen.getByText('open gate'))
    await screen.findByText('Only question?')
    await userEvent.keyboard('1g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await userEvent.click(await screen.findByRole('button', { name: /^done$/i }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('sends the owner to the reader page that needs restudy', async () => {
    setup(null)
    mount()
    await userEvent.click(screen.getByText('open gate'))
    await screen.findByText('Only question?')
    await userEvent.keyboard('1g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await userEvent.click(await screen.findByRole('button', { name: /review page 12/i }))
    await waitFor(() => expect(screen.getByLabelText('path')).toHaveTextContent('/study'))
    expect(screen.getByLabelText('request')).toHaveTextContent('7:12')
  })
})
