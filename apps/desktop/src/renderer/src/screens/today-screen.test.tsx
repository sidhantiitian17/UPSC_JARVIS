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

let progress: object | null = null
function setup(
  d: object,
  queue: object[] = [],
  prog: object | null = null
): ReturnType<typeof vi.fn> {
  progress = prog
  const api = vi.fn(async (req: { path: string }) => {
    if (req.path === '/dashboard/today') return { status: 200, body: d }
    if (req.path === '/review/queue') return { status: 200, body: queue }
    if (req.path === '/gamification/progress')
      return progress ? { status: 200, body: progress } : { status: 404, body: null }
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
const prog = (over: object = {}): object => ({
  xp_total: 250,
  level: 2,
  xp_into_level: 150,
  xp_to_next_level: 50,
  streak: 5,
  best_streak: 9,
  freezes: 1,
  at_risk: false,
  today_minutes: 40,
  today_goal: 60,
  daily_goal_minutes: 60,
  bad_day_goal_minutes: 20,
  comeback: { active: false, lost_streak: 0, days_done: 0, days_needed: 3 },
  events: [],
  ...over
})
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

  it('shows level, XP towards the next level, streak and freezes, with honest wording', async () => {
    setup(dash({ verified_minutes_today: 40 }), [], prog())
    renderToday()
    expect(await screen.findByText(/level 2/i)).toBeInTheDocument()
    expect(screen.getByText(/250 xp/i)).toBeInTheDocument()
    const bar = screen.getByRole('progressbar', { name: /xp to level 3/i })
    expect(bar).toHaveAttribute('aria-valuenow', '75')
    expect(screen.getByText(/5-day streak/i)).toBeInTheDocument()
    expect(screen.getByText(/1 streak freeze/i)).toBeInTheDocument()
    expect(screen.getByText(/40 of 60 min today/i)).toBeInTheDocument()
    expect(
      screen.getByText(/xp comes only from minutes that passed the recall gate/i)
    ).toBeInTheDocument()
  })

  it('is supportive, never shaming, when the streak is at risk or paused', async () => {
    setup(dash(), [], prog({ at_risk: true, today_minutes: 10 }))
    renderToday()
    expect(await screen.findByText(/50 more min keeps your streak going/i)).toBeInTheDocument()
    expect(document.body.textContent?.toLowerCase()).not.toMatch(/lost|fail|lazy|shame|behind/)
  })

  it('shows an open comeback quest', async () => {
    setup(
      dash(),
      [],
      prog({ streak: 2, comeback: { active: true, lost_streak: 8, days_done: 2, days_needed: 3 } })
    )
    renderToday()
    expect(await screen.findByText(/comeback quest: 2 of 3 goal days/i)).toBeInTheDocument()
  })

  it('keeps one primary action even with the progress card', async () => {
    setup(dash({ due_cards: 3, review_remaining_today: 40 }), [], prog())
    renderToday()
    await screen.findByText(/level 2/i)
    expect(primaries()).toHaveLength(1)
  })
})
