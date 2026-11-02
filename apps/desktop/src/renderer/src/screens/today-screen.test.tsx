import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { TodayScreen } from './today-screen'

const heat = (last = 0): object[] =>
  Array.from({ length: 84 }, (_, i) => ({
    date: `2026-08-${String((i % 28) + 1).padStart(2, '0')}`,
    minutes: i === 83 ? last : 0
  }))
const dash = (over: object = {}): object => ({
  verified_minutes_today: 0,
  verified_minutes_week: 0,
  heatmap: heat(),
  next_block: null,
  awaiting_gate_session_id: null,
  due_cards: 0,
  review_remaining_today: 40,
  ...over
})

function setup(d: object, queue: object[] = []): ReturnType<typeof vi.fn> {
  const api = vi.fn(async (req: { path: string }) => {
    if (req.path === '/dashboard/today') return { status: 200, body: d }
    if (req.path === '/review/queue') return { status: 200, body: queue }
    if (req.path.endsWith('/rate'))
      return { status: 200, body: { card_id: 1, due: 'x', interval_days: 1 } }
    return { status: 404, body: null }
  })
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true })
  }
  return api
}
const renderToday = (): void => {
  render(
    <MemoryRouter>
      <TodayScreen />
    </MemoryRouter>
  )
}
const primaries = (): HTMLElement[] =>
  screen.getAllByRole('button').filter((b) => b.getAttribute('data-variant') === 'primary')

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('Today screen', () => {
  it('with nothing to do it has an empty state and one primary action to start studying', async () => {
    setup(dash())
    renderToday()
    expect(await screen.findByTestId('empty-state')).toBeInTheDocument()
    expect(primaries()).toHaveLength(1)
    expect(primaries()[0]).toHaveTextContent(/start studying/i)
  })

  it('shows verified retained minutes for today and this week, labelled honestly', async () => {
    setup(dash({ verified_minutes_today: 50, verified_minutes_week: 180 }))
    renderToday()
    expect(await screen.findByText(/50 min verified today/i)).toBeInTheDocument()
    expect(screen.getByText(/180 min verified this week/i)).toBeInTheDocument()
    expect(screen.getByText(/passed the recall gate/i)).toBeInTheDocument()
  })

  it('renders a 12-week heatmap whose cells carry numbers, not only colour', async () => {
    setup(dash({ heatmap: heat(45) }))
    renderToday()
    const grid = await screen.findByRole('img', { name: /last 12 weeks/i })
    expect(grid.querySelectorAll('[data-cell]')).toHaveLength(84)
    expect(grid.querySelector('[data-cell][title*="45 min"]')).not.toBeNull()
  })

  it('shows due cards and makes Start review the single primary action', async () => {
    setup(
      dash({
        due_cards: 12,
        review_remaining_today: 30,
        next_block: { document_id: 7, title: 'Polity', page: 12 }
      })
    )
    renderToday()
    expect(await screen.findByText(/12 cards due/i)).toBeInTheDocument()
    expect(screen.getByText(/30 left today/i)).toBeInTheDocument()
    expect(primaries()).toHaveLength(1)
    expect(primaries()[0]).toHaveTextContent(/start review/i)
    expect(screen.getByRole('button', { name: /continue reading/i })).toBeInTheDocument()
  })

  it('offers Continue reading as the primary action when nothing is due', async () => {
    setup(dash({ next_block: { document_id: 7, title: 'Polity', page: 12 } }))
    renderToday()
    expect(await screen.findByText(/polity, page 12/i)).toBeInTheDocument()
    expect(primaries()).toHaveLength(1)
    expect(primaries()[0]).toHaveTextContent(/continue reading/i)
  })

  it('puts a waiting recall gate first', async () => {
    setup(dash({ awaiting_gate_session_id: 4, due_cards: 3, review_remaining_today: 40 }))
    renderToday()
    expect(await screen.findByText(/recall gate is waiting/i)).toBeInTheDocument()
    expect(primaries()).toHaveLength(1)
    expect(primaries()[0]).toHaveTextContent(/finish recall gate/i)
  })

  it('opens the review session and comes back', async () => {
    setup(dash({ due_cards: 1 }), [
      {
        card_id: 1,
        question_id: 1,
        subject: 's',
        due: 'x',
        stem: 'Due card?',
        options: ['a', 'b', 'c', 'd'],
        answer_index: 0,
        explanation: '',
        source_quote: 'q'
      }
    ])
    renderToday()
    await userEvent.click(await screen.findByRole('button', { name: /start review/i }))
    expect(await screen.findByText('Due card?')).toBeInTheDocument()
    await userEvent.keyboard('1')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('3')
    await userEvent.click(await screen.findByRole('button', { name: /done/i }))
    await waitFor(() =>
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/today/i)
    )
  })
})
