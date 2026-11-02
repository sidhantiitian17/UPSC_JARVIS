import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { GateView } from './gate-view'

const Q = (id: number, stem: string): object => ({
  id,
  stem,
  options: ['Alpha', 'Beta', 'Gamma', 'Delta'],
  style: 'recall',
  source: 'generated',
  interleaved: false,
  chunk_id: id * 10,
  page: 100 + id,
  ordinal: 0
})
const gate = (over: object = {}): object => ({
  session_id: 3,
  questions: [Q(1, 'First question?'), Q(2, 'Second question?')],
  discarded: 0,
  fallback_used: false,
  short_range: false,
  ...over
})
const KEY: Record<number, number> = { 1: 1, 2: 2 } // correct option index per question

type Res = { status: number; body: unknown }
function setup(opts: {
  gate?: object | Res
  result?: object
  failFinish?: boolean
  skipResult?: object
}): ReturnType<typeof vi.fn> {
  const api = vi.fn(
    async (req: {
      method: string
      path: string
      body?: Record<string, number | string>
    }): Promise<Res> => {
      if (req.path === '/sessions/3/gate' && req.method === 'POST') {
        const g = opts.gate ?? gate()
        return 'status' in (g as object) ? (g as Res) : { status: 200, body: g }
      }
      if (req.path === '/sessions/3/gate/answer') {
        const qid = Number(req.body?.question_id)
        const chosen = Number(req.body?.chosen_index)
        return {
          status: 200,
          body: {
            question_id: qid,
            correct: chosen === KEY[qid],
            chosen_index: chosen,
            answer_index: KEY[qid],
            explanation: `Because of fact ${qid}.`,
            source_quote: `Quote ${qid} from the book.`,
            chunk_id: qid * 10,
            page: 100 + qid,
            ordinal: 0
          }
        }
      }
      if (req.path === '/sessions/3/gate/finish')
        return {
          status: 200,
          body: opts.result ?? {
            session_id: 3,
            total: 2,
            correct: 2,
            retention_pct: 100,
            passed: true,
            skipped: false,
            xp: 42,
            pass_mark: 70,
            restudy: [],
            nodes: [{ id: 'gs2.polity', title: 'Constitution and Polity' }]
          }
        }
      if (req.path === '/sessions/3/gate/skip')
        return {
          status: 200,
          body: opts.skipResult ?? {
            session_id: 3,
            total: 2,
            correct: 0,
            retention_pct: 0,
            passed: false,
            skipped: true,
            xp: 0,
            pass_mark: 70,
            restudy: [],
            nodes: []
          }
        }
      if (req.path.startsWith('/questions/') && req.path.endsWith('/report'))
        return { status: 200, body: { question_id: 1, status: 'reported' } }
      return { status: 404, body: null }
    }
  )
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

const open = (onClose = vi.fn()): ReturnType<typeof vi.fn> => {
  render(<GateView sessionId={3} documentId={7} onClose={onClose} />)
  return onClose
}

describe('GateView', () => {
  it('is a full-window dialog that builds the gate then shows question 1 of N', async () => {
    setup({})
    open()
    expect(screen.getByRole('dialog', { name: /recall gate/i })).toBeInTheDocument()
    expect(await screen.findByText('First question?')).toBeInTheDocument()
    expect(screen.getByText(/question 1 of 2/i)).toBeInTheDocument()
    expect(screen.getAllByRole('radio')).toHaveLength(4)
  })

  it('answers with keys: 2 picks the option, B confidence tag submits and reveals the result', async () => {
    const api = setup({})
    open()
    await screen.findByText('First question?')
    await userEvent.keyboard('2')
    expect(screen.getByRole('radio', { name: /beta/i })).toBeChecked()
    await userEvent.keyboard('g')
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        expect.objectContaining({
          method: 'POST',
          path: '/sessions/3/gate/answer',
          body: expect.objectContaining({ question_id: 1, chosen_index: 1, confidence: 'G' })
        })
      )
    )
    expect(
      await screen.findByText(/correct/i, { selector: '[data-testid="verdict"]' })
    ).toBeInTheDocument()
    expect(screen.getByText(/because of fact 1/i)).toBeInTheDocument()
    expect(screen.getByText(/quote 1 from the book/i)).toBeInTheDocument()
    expect(screen.getByText(/page 101/i)).toBeInTheDocument()
  })

  it('shows the right option when the answer is wrong', async () => {
    setup({})
    open()
    await screen.findByText('First question?')
    await userEvent.keyboard('1')
    await userEvent.keyboard('r')
    const verdict = await screen.findByTestId('verdict')
    expect(verdict).toHaveTextContent(/incorrect/i)
    expect(verdict).toHaveTextContent(/beta/i)
  })

  it('confidence tags can be clicked and always pair colour with a letter', async () => {
    setup({})
    open()
    await screen.findByText('First question?')
    await userEvent.click(screen.getByRole('radio', { name: /beta/i }))
    const group = screen.getByRole('group', { name: /how sure are you/i })
    expect(within(group).getByRole('button', { name: /green/i })).toHaveTextContent('G')
    expect(within(group).getByRole('button', { name: /amber/i })).toHaveTextContent('A')
    expect(within(group).getByRole('button', { name: /red/i })).toHaveTextContent('R')
    await userEvent.click(within(group).getByRole('button', { name: /amber/i }))
    expect(await screen.findByTestId('verdict')).toBeInTheDocument()
  })

  it('walks through all questions and shows a passing result without any "predicted marks" claim', async () => {
    setup({})
    open()
    await screen.findByText('First question?')
    await userEvent.keyboard('2g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByText('Second question?')
    expect(screen.getByText(/question 2 of 2/i)).toBeInTheDocument()
    await userEvent.keyboard('3g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    const result = await screen.findByRole('region', { name: /gate result/i })
    expect(within(result).getByText(/100%/)).toBeInTheDocument()
    expect(within(result).getByText(/passed/i)).toBeInTheDocument()
    expect(within(result).getByText(/\+42 xp/i)).toBeInTheDocument()
    expect(within(result).getByText('Constitution and Polity')).toBeInTheDocument()
    expect(document.body.textContent?.toLowerCase()).not.toContain('predicted')
  })

  it('a failed gate gives restudy advice and says coverage did not increase', async () => {
    setup({
      result: {
        session_id: 3,
        total: 2,
        correct: 0,
        retention_pct: 0,
        passed: false,
        skipped: false,
        xp: 0,
        pass_mark: 70,
        restudy: [
          {
            chunk_id: 10,
            book: 'Laxmikanth',
            page: 141,
            ordinal: 1,
            quote: 'The Speaker presides.'
          }
        ],
        nodes: []
      }
    })
    const onClose = open()
    await screen.findByText('First question?')
    await userEvent.keyboard('1a')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByText('Second question?')
    await userEvent.keyboard('1a')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    const result = await screen.findByRole('region', { name: /gate result/i })
    expect(within(result).getByText(/not passed/i)).toBeInTheDocument()
    expect(within(result).getByText(/coverage did not increase/i)).toBeInTheDocument()
    expect(within(result).getByText(/Laxmikanth/)).toBeInTheDocument()
    expect(within(result).getByText(/page 141/i)).toBeInTheDocument()
    expect(within(result).getByText(/paragraph 2/i)).toBeInTheDocument()
    await userEvent.click(within(result).getByRole('button', { name: /review page 141/i }))
    expect(onClose).toHaveBeenCalledWith({ openPage: { documentId: 7, page: 141 } })
  })

  it('reporting a bad question removes it from the gate', async () => {
    const api = setup({})
    open()
    await screen.findByText('First question?')
    await userEvent.click(screen.getByRole('button', { name: /report bad question/i }))
    expect(api).toHaveBeenCalledWith({
      method: 'POST',
      path: '/questions/1/report',
      body: { reason: '' }
    })
    expect(await screen.findByText('Second question?')).toBeInTheDocument()
    expect(screen.getByText(/question 1 of 1/i)).toBeInTheDocument()
  })

  it('emergency skip asks for confirmation and states the cost', async () => {
    const api = setup({})
    open()
    await screen.findByText('First question?')
    await userEvent.click(screen.getByRole('button', { name: /emergency skip/i }))
    const confirm = await screen.findByRole('alertdialog')
    expect(confirm).toHaveTextContent(/no coverage/i)
    expect(confirm).toHaveTextContent(/double/i)
    await userEvent.click(within(confirm).getByRole('button', { name: /skip anyway/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(expect.objectContaining({ path: '/sessions/3/gate/skip' }))
    )
    expect(await screen.findByText(/gate skipped/i)).toBeInTheDocument()
  })

  it('tells the owner when the quiz was built offline', async () => {
    setup({ gate: gate({ fallback_used: true }) })
    open()
    expect(await screen.findByText(/built offline/i)).toBeInTheDocument()
  })

  it('shows a friendly error with a way out when the gate cannot be built', async () => {
    setup({
      gate: {
        status: 422,
        body: { detail: 'This range has no readable text to build questions from.' }
      }
    })
    const onClose = open()
    expect(await screen.findByRole('alert')).toHaveTextContent(/no readable text/i)
    await userEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('lets the owner leave without penalty when the gate could not be built', async () => {
    const api = setup({
      gate: { status: 422, body: { detail: 'Jarvis could not build questions from this range.' } }
    })
    const onClose = open()
    await screen.findByRole('alert')
    await userEvent.click(screen.getByRole('button', { name: /skip this gate/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/sessions/3/gate/skip',
        body: { penalty: false }
      })
    )
    await userEvent.click(await screen.findByRole('button', { name: /^close$/i }))
    expect(onClose).toHaveBeenCalled()
  })

  it('tells the pet about a pass, with the retention', async () => {
    setup({})
    const pet = vi.fn(async () => true)
    ;(window as unknown as { jarvis: { pet: unknown } }).jarvis.pet = { event: pet }
    open()
    await screen.findByText('First question?')
    await userEvent.keyboard('2g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByText('Second question?')
    await userEvent.keyboard('3g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByRole('region', { name: /gate result/i })
    expect(pet).toHaveBeenCalledWith('gate_pass', { retentionPct: 100 })
  })

  it('tells the pet when the gate was not passed', async () => {
    setup({
      result: {
        session_id: 3,
        total: 2,
        correct: 0,
        retention_pct: 0,
        passed: false,
        skipped: false,
        xp: 0,
        pass_mark: 70,
        restudy: [],
        nodes: []
      }
    })
    const pet = vi.fn(async () => true)
    ;(window as unknown as { jarvis: { pet: unknown } }).jarvis.pet = { event: pet }
    open()
    await screen.findByText('First question?')
    await userEvent.keyboard('1a')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByText('Second question?')
    await userEvent.keyboard('1a')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByRole('region', { name: /gate result/i })
    expect(pet).toHaveBeenCalledWith('gate_not_passed', { retentionPct: 0 })
  })

  it('tells the pet about a level-up when the level rose during the gate', async () => {
    const api = setup({})
    const levels = [2, 3]
    const base = (
      window as unknown as { jarvis: { api: (r: { path: string }) => Promise<unknown> } }
    ).jarvis.api
    ;(window as unknown as { jarvis: { api: unknown; pet: unknown } }).jarvis.api = vi.fn(
      async (req: { path: string; method: string; body?: unknown }) =>
        req.path === '/gamification/progress'
          ? { status: 200, body: { level: levels.shift() ?? 3 } }
          : (api as unknown as (r: unknown) => Promise<unknown>)(req)
    )
    void base
    const pet = vi.fn(async () => true)
    ;(window as unknown as { jarvis: { pet: unknown } }).jarvis.pet = { event: pet }
    open()
    await screen.findByText('First question?')
    await userEvent.keyboard('2g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByText('Second question?')
    await userEvent.keyboard('3g')
    await screen.findByTestId('verdict')
    await userEvent.keyboard('{Enter}')
    await screen.findByRole('region', { name: /gate result/i })
    await waitFor(() => expect(pet).toHaveBeenCalledWith('level_up', { level: 3 }))
  })
})
