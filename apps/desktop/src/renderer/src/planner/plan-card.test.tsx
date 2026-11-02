import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PlanCard } from './plan-card'

const PLAN = {
  free_minutes: 240,
  planned_minutes: 230,
  catch_up: false,
  notes: [],
  blocks: [
    { kind: 'review', subject_id: null, subject: null, minutes: 12, reason: '12 cards due' },
    {
      kind: 'study',
      subject_id: 'gs2.polity',
      subject: 'Polity & Constitution',
      minutes: 50,
      reason: 'weakest area: 20% recall'
    },
    { kind: 'break', subject_id: null, subject: null, minutes: 10, reason: 'rest' }
  ]
}
const STATUS = { committed_today: null, yesterday: null, catch_up_due: false }

function setup(opts: { status?: object; plan?: object } = {}): ReturnType<typeof vi.fn> {
  const api = vi.fn(async (req: { method: string; path: string }) => {
    if (req.path === '/planner/status') return { status: 200, body: opts.status ?? STATUS }
    if (req.path === '/planner/plan') return { status: 200, body: opts.plan ?? PLAN }
    if (req.path === '/planner/commit')
      return { status: 200, body: { free_minutes: 240, study_minutes: 50, blocks: PLAN.blocks } }
    return { status: 404, body: null }
  })
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true })
  }
  return api
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('PlanCard', () => {
  it('asks how many hours are free and builds the plan', async () => {
    const api = setup()
    render(<PlanCard />)
    const hours = await screen.findByRole('spinbutton', { name: /free hours/i })
    await userEvent.clear(hours)
    await userEvent.type(hours, '4')
    await userEvent.click(screen.getByRole('button', { name: /make plan/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/planner/plan',
        body: { free_hours: 4 }
      })
    )
    const list = await screen.findByRole('list', { name: /today's plan/i })
    expect(within(list).getByText(/review/i)).toBeInTheDocument()
    expect(within(list).getByText(/Polity & Constitution/)).toBeInTheDocument()
    expect(within(list).getByText(/weakest area: 20% recall/)).toBeInTheDocument()
    expect(screen.getByText(/230 of 240 min planned/i)).toBeInTheDocument()
  })

  it('commits the plan and confirms it', async () => {
    const api = setup()
    render(<PlanCard />)
    await userEvent.click(await screen.findByRole('button', { name: /make plan/i }))
    await userEvent.click(await screen.findByRole('button', { name: /commit to this plan/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/planner/commit',
        body: { free_hours: 4 }
      })
    )
    expect(await screen.findByText(/plan committed/i)).toBeInTheDocument()
  })

  it('shows a gentle catch-up note when yesterday was only partly verified', async () => {
    setup({
      status: {
        committed_today: null,
        yesterday: { committed_minutes: 200, verified_minutes: 60, missed: true },
        catch_up_due: true
      },
      plan: {
        ...PLAN,
        catch_up: true,
        notes: [
          "Yesterday's plan was only partly verified. A short catch-up recall gate comes first."
        ]
      }
    })
    render(<PlanCard />)
    expect(await screen.findByText(/60 of 200 min verified/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /make plan/i }))
    expect(await screen.findByText(/catch-up recall gate comes first/i)).toBeInTheDocument()
    expect(document.body.textContent?.toLowerCase()).not.toMatch(
      /lazy|fail|shame|behind|missed your/
    )
  })

  it('shows an already committed plan for today', async () => {
    setup({
      status: {
        committed_today: { free_minutes: 240, study_minutes: 100, blocks: PLAN.blocks },
        yesterday: null,
        catch_up_due: false
      }
    })
    render(<PlanCard />)
    expect(await screen.findByText(/committed to 100 min of study today/i)).toBeInTheDocument()
  })

  it('refuses free hours outside 1 to 16 before calling the service', async () => {
    const api = setup()
    render(<PlanCard />)
    const hours = await screen.findByRole('spinbutton', { name: /free hours/i })
    await userEvent.clear(hours)
    await userEvent.type(hours, '20')
    await userEvent.click(screen.getByRole('button', { name: /make plan/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/between 1 and 16/i)
    expect(api).not.toHaveBeenCalledWith(expect.objectContaining({ path: '/planner/plan' }))
  })
})
