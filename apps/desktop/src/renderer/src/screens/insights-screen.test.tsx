import { render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { InsightsScreen } from './insights-screen'

const day = (i: number, c: number, v: number): object => ({
  date: `2026-11-0${i}`,
  claimed_hours: c,
  verified_hours: v
})
const TRUTH = {
  weekly: {
    days: [
      day(1, 2, 1),
      day(2, 0, 0),
      day(3, 3, 0),
      day(4, 1, 1),
      day(5, 0, 0),
      day(6, 2, 2),
      day(7, 1, 0)
    ],
    claimed_hours: 9,
    verified_hours: 4,
    verified_share: 44
  },
  calibration: [
    { tag: 'G', answers: 10, accuracy: 90, enough_data: true, expected: '90%+' },
    { tag: 'A', answers: 10, accuracy: 30, enough_data: true, expected: '60-70%' },
    { tag: 'R', answers: 2, accuracy: 50, enough_data: false, expected: '10-30%' }
  ],
  forecast: {
    exam_date: '2028-05-28',
    assumed_exam_date: true,
    days_left: 570,
    avg_daily_verified_minutes: 60,
    projected_verified_hours: 570
  },
  report: [
    'In the last 7 days you verified 4 h of the 9 h you claimed (44%).',
    'Another kind sentence.'
  ]
}

type Res = { status: number; body: unknown }
function setup(res: Res): void {
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api: vi.fn(async () => res),
    status: async () => ({ ready: true })
  }
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('Insights (Truth Dashboard)', () => {
  it('shows claimed next to verified hours with the share', async () => {
    setup({ status: 200, body: TRUTH })
    render(<InsightsScreen />)
    const card = await screen.findByRole('region', { name: /claimed versus verified/i })
    expect(within(card).getByText(/9 h claimed/i)).toBeInTheDocument()
    expect(within(card).getByText(/4 h verified/i)).toBeInTheDocument()
    expect(within(card).getByText(/44% verified/i)).toBeInTheDocument()
    expect(within(card).getAllByTestId('day-row')).toHaveLength(7)
  })

  it('shows calibration per tag with accuracy, expected band and data warnings', async () => {
    setup({ status: 200, body: TRUTH })
    render(<InsightsScreen />)
    const table = await screen.findByRole('table', { name: /calibration/i })
    const rows = within(table).getAllByRole('row')
    expect(rows).toHaveLength(4)
    expect(within(rows[1]).getByText('G')).toBeInTheDocument()
    expect(within(rows[1]).getByText('90%')).toBeInTheDocument()
    expect(within(rows[2]).getByText(/60-70%/)).toBeInTheDocument()
    expect(within(rows[3]).getByText(/not enough data/i)).toBeInTheDocument()
  })

  it('shows the forecast and says when the exam date is assumed', async () => {
    setup({ status: 200, body: TRUTH })
    render(<InsightsScreen />)
    expect(await screen.findByText(/570 days left/i)).toBeInTheDocument()
    expect(screen.getByText(/60 verified min per day/i)).toBeInTheDocument()
    expect(screen.getByText(/assumed exam date/i)).toBeInTheDocument()
  })

  it('lists the weekly honesty report and never shows predicted marks', async () => {
    setup({ status: 200, body: TRUTH })
    render(<InsightsScreen />)
    expect(await screen.findByText(/verified 4 h of the 9 h you claimed/i)).toBeInTheDocument()
    expect(screen.getByText('Another kind sentence.')).toBeInTheDocument()
    expect(document.body.textContent?.toLowerCase()).not.toContain('predicted')
  })

  it('shows a friendly error when the data cannot load', async () => {
    setup({ status: 500, body: null })
    render(<InsightsScreen />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load/i)
  })
})
