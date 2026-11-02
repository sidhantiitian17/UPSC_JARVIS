import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ReviewSession } from './review-session'

const card = (id: number, stem: string, answer = 1): object => ({
  card_id: id,
  question_id: id + 100,
  subject: 'gs2.polity',
  due: '2026-11-01T00:00:00Z',
  stem,
  options: ['Alpha', 'Beta', 'Gamma', 'Delta'],
  answer_index: answer,
  explanation: `Because ${stem}`,
  source_quote: `Quote for ${stem}`
})

type Res = { status: number; body: unknown }
function setup(queue: object[] | Res): ReturnType<typeof vi.fn> {
  const api = vi.fn(async (req: { method: string; path: string; body?: unknown }): Promise<Res> => {
    if (req.path === '/review/queue')
      return Array.isArray(queue) ? { status: 200, body: queue } : queue
    if (req.path.endsWith('/rate'))
      return { status: 200, body: { card_id: 1, due: '2026-11-05T00:00:00Z', interval_days: 3.2 } }
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

describe('ReviewSession', () => {
  it('shows the first due card with progress', async () => {
    setup([card(1, 'First?'), card(2, 'Second?')])
    render(<ReviewSession onClose={() => {}} />)
    expect(await screen.findByText('First?')).toBeInTheDocument()
    expect(screen.getByText(/card 1 of 2/i)).toBeInTheDocument()
    expect(screen.getAllByRole('radio')).toHaveLength(4)
  })

  it('choosing an option reveals the answer, explanation and source, then rating moves on', async () => {
    const api = setup([card(1, 'First?'), card(2, 'Second?')])
    render(<ReviewSession onClose={() => {}} />)
    await screen.findByText('First?')
    await userEvent.keyboard('3')
    const verdict = await screen.findByTestId('verdict')
    expect(verdict).toHaveTextContent(/incorrect/i)
    expect(verdict).toHaveTextContent(/beta/i)
    expect(screen.getByText(/because first\?/i)).toBeInTheDocument()
    expect(screen.getByText(/quote for first\?/i)).toBeInTheDocument()
    await userEvent.keyboard('1') // rate: Again
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/review/cards/1/rate',
        body: { rating: 1 }
      })
    )
    expect(await screen.findByText('Second?')).toBeInTheDocument()
    expect(screen.getByText(/card 2 of 2/i)).toBeInTheDocument()
  })

  it('offers Again, Hard, Good and Easy buttons after the reveal', async () => {
    const api = setup([card(1, 'First?')])
    render(<ReviewSession onClose={() => {}} />)
    await userEvent.click(await screen.findByRole('radio', { name: /beta/i }))
    for (const name of ['Again', 'Hard', 'Good', 'Easy']) {
      expect(screen.getByRole('button', { name: new RegExp(`^${name}`, 'i') })).toBeInTheDocument()
    }
    await userEvent.click(screen.getByRole('button', { name: /^good/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/review/cards/1/rate',
        body: { rating: 3 }
      })
    )
  })

  it('finishes with a summary and a close button', async () => {
    const onClose = vi.fn()
    setup([card(1, 'Only?')])
    render(<ReviewSession onClose={onClose} />)
    await screen.findByText('Only?')
    await userEvent.keyboard('2')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('3')
    expect(await screen.findByText(/1 card reviewed/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /done/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('says so when nothing is due', async () => {
    setup([])
    render(<ReviewSession onClose={() => {}} />)
    expect(await screen.findByText(/nothing is due/i)).toBeInTheDocument()
  })

  it('shows a friendly error when the queue cannot load', async () => {
    setup({ status: 500, body: null })
    render(<ReviewSession onClose={() => {}} />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load/i)
  })
})
