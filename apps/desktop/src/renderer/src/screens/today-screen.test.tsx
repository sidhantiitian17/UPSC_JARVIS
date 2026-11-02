import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { TodayScreen } from './today-screen'

function setup(stats: object, queue: object[] = []): void {
  const api = vi.fn(async (req: { path: string }) => {
    if (req.path === '/review/stats') return { status: 200, body: stats }
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
}
const stats = (over: object = {}): object => ({
  due_now: 0,
  daily_limit: 40,
  reviewed_today: 0,
  remaining_today: 40,
  total_cards: 0,
  ...over
})
const renderToday = (): void => {
  render(
    <MemoryRouter>
      <TodayScreen />
    </MemoryRouter>
  )
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('Today screen', () => {
  it('with nothing due it has an empty state and one primary action to start studying', async () => {
    setup(stats())
    renderToday()
    expect(await screen.findByTestId('empty-state')).toBeInTheDocument()
    const primary = screen
      .getAllByRole('button')
      .filter((b) => b.getAttribute('data-variant') === 'primary')
    expect(primary).toHaveLength(1)
    expect(primary[0]).toHaveTextContent(/study/i)
  })

  it('shows due cards and the daily allowance, with Start review as the primary action', async () => {
    setup(stats({ due_now: 12, remaining_today: 30, reviewed_today: 10, total_cards: 50 }))
    renderToday()
    expect(await screen.findByText(/12 cards due/i)).toBeInTheDocument()
    expect(screen.getByText(/30 left today/i)).toBeInTheDocument()
    const primary = screen
      .getAllByRole('button')
      .filter((b) => b.getAttribute('data-variant') === 'primary')
    expect(primary).toHaveLength(1)
    expect(primary[0]).toHaveTextContent(/start review/i)
  })

  it('opens the review session and comes back', async () => {
    setup(stats({ due_now: 1, remaining_today: 40 }), [
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
