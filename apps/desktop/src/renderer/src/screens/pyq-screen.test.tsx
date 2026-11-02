import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PyqScreen } from './pyq-screen'

const paper = (over: object = {}): object => ({
  phase: 'prelims',
  year: 2023,
  paper: 'gs-paper-1',
  total: 100,
  parsed: 94,
  failed: 6,
  reviewed: 0,
  verified: 0,
  ...over
})
const q = (over: object = {}): object => ({
  id: 'PRE-2023-GS1-001',
  phase: 'prelims',
  year: 2023,
  paper: 'gs-paper-1',
  number: 1,
  page: 3,
  marks: null,
  negative_marks: null,
  stem: 'Consider the following trees',
  options: ['Only one', 'Only two', 'All three', 'None'],
  raw_text: null,
  answer: null,
  answer_source: 'none',
  suggested_answer: null,
  status: 'parsed',
  source_url: 'https://www.upsc.gov.in/x.pdf',
  source_sha256: 'a'.repeat(64),
  tags: [],
  ...over
})

type Res = { status: number; body: unknown }
function setup(
  opts: { papers?: object[]; questions?: object[]; verify?: Res; imported?: object } = {}
): ReturnType<typeof vi.fn> {
  let papers = opts.papers ?? []
  const api = vi.fn(async (req: { method: string; path: string; body?: unknown }): Promise<Res> => {
    if (req.path === '/pyq/papers') return { status: 200, body: papers }
    if (req.path === '/pyq/import') {
      papers = [paper()]
      return {
        status: 200,
        body: opts.imported ?? {
          files: 22,
          questions: 1587,
          inserted: 1587,
          updated: 0,
          kept_owner_edits: 0
        }
      }
    }
    if (req.path.startsWith('/pyq/questions?'))
      return {
        status: 200,
        body: opts.questions ?? [
          q(),
          q({
            id: 'PRE-2023-GS1-002',
            number: 2,
            status: 'failed',
            stem: '',
            options: [],
            raw_text: 'raw ocr text'
          })
        ]
      }
    if (req.path === '/syllabus/tree')
      return {
        status: 200,
        body: [
          {
            id: 'gs2',
            parent_id: null,
            title: 'GS Paper II',
            kind: 'paper',
            paper: 'GS2',
            reviewed: false,
            source: 'owner',
            children: [
              {
                id: 'gs2.polity',
                parent_id: 'gs2',
                title: 'Constitution and Polity',
                kind: 'subject',
                paper: 'GS2',
                reviewed: false,
                source: 'owner',
                children: []
              }
            ]
          }
        ]
      }
    if (req.path.endsWith('/suggest-tags'))
      return {
        status: 200,
        body: [
          {
            node_id: 'gs2.polity',
            title: 'Constitution and Polity',
            status: 'suggested',
            source: 'llm'
          }
        ]
      }
    if (req.method === 'PUT' && req.path.includes('/tags/'))
      return {
        status: 200,
        body: [
          {
            node_id: 'gs2.polity',
            title: 'Constitution and Polity',
            status:
              (req.body as { decision: string }).decision === 'accept' ? 'accepted' : 'rejected',
            source: 'llm'
          }
        ]
      }
    if (req.method === 'POST' && req.path.endsWith('/tags'))
      return {
        status: 200,
        body: [
          {
            node_id: (req.body as { node_id: string }).node_id,
            title: 'Constitution and Polity',
            status: 'accepted',
            source: 'owner'
          }
        ]
      }
    if (req.method === 'PUT')
      return {
        status: 200,
        body: q({ ...(req.body as object), id: req.path.split('/').pop(), status: 'reviewed' })
      }
    if (req.path.endsWith('/verify'))
      return opts.verify ?? { status: 200, body: q({ status: 'verified' }) }
    return { status: 404, body: null }
  })
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true })
  }
  return api
}
const primaries = (): HTMLElement[] =>
  screen.getAllByRole('button').filter((b) => b.getAttribute('data-variant') === 'primary')

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('PYQ screen', () => {
  it('starts with an empty state whose single primary action imports the dataset', async () => {
    const api = setup()
    render(<PyqScreen />)
    expect(await screen.findByTestId('empty-state')).toBeInTheDocument()
    expect(primaries()).toHaveLength(1)
    await userEvent.click(primaries()[0])
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({ method: 'POST', path: '/pyq/import', body: {} })
    )
    expect(await screen.findByText(/imported 1587 questions/i)).toBeInTheDocument()
    expect(await screen.findByText(/prelims 2023/i)).toBeInTheDocument()
  })

  it('lists papers with honest counts', async () => {
    setup({ papers: [paper()] })
    render(<PyqScreen />)
    const row = await screen.findByRole('listitem', { name: /prelims 2023 gs-paper-1/i })
    expect(within(row).getByText(/94 parsed/)).toBeInTheDocument()
    expect(within(row).getByText(/6 failed/)).toBeInTheDocument()
    expect(within(row).getByText(/0 verified/)).toBeInTheDocument()
  })

  it('opens a paper, filters by status and shows each question with a status label', async () => {
    const api = setup({ papers: [paper()] })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    expect(await screen.findByText(/Consider the following trees/)).toBeInTheDocument()
    expect(screen.getAllByText('Failed').length).toBeGreaterThan(1) // the badge and the filter option
    await userEvent.selectOptions(screen.getByRole('combobox', { name: /status/i }), 'failed')
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(
        expect.objectContaining({ path: expect.stringContaining('status=failed') })
      )
    )
  })

  it('edits a question: text, options and answer, saved through the service', async () => {
    const api = setup({ papers: [paper()] })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 1/i }))
    const stem = await screen.findByRole('textbox', { name: /question text/i })
    await userEvent.clear(stem)
    await userEvent.type(stem, 'Fixed text')
    await userEvent.selectOptions(screen.getByRole('combobox', { name: /answer/i }), 'b')
    await userEvent.click(screen.getByRole('button', { name: /^save$/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/pyq/questions/PRE-2023-GS1-001',
        body: {
          stem: 'Fixed text',
          options: ['Only one', 'Only two', 'All three', 'None'],
          answer: 'b'
        }
      })
    )
  })

  it('says where answers come from and never offers an AI-filled key', async () => {
    setup({ papers: [paper()] })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 1/i }))
    expect(await screen.findByText(/only from the official key or from you/i)).toBeInTheDocument()
    expect(screen.getByText(/source: https:\/\/www.upsc.gov.in\/x.pdf/i)).toBeInTheDocument()
  })

  it('shows the raw text of a failed question next to the editor', async () => {
    setup({ papers: [paper()] })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 2/i }))
    expect(await screen.findByText('raw ocr text')).toBeInTheDocument()
  })

  it('marks a question verified and shows the server reason when it cannot', async () => {
    setup({
      papers: [paper()],
      verify: {
        status: 422,
        body: { detail: 'A verified question needs four options, all filled in.' }
      }
    })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 2/i }))
    await userEvent.click(await screen.findByRole('button', { name: /mark verified/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/needs four options/i)
  })

  it('shows a friendly error when the service is not reachable', async () => {
    ;(window as unknown as { jarvis: unknown }).jarvis = {
      platform: 'test',
      api: vi.fn(async () => ({ status: 500, body: null })),
      status: async () => ({ ready: true })
    }
    render(<PyqScreen />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load/i)
  })

  it('shows existing tags with their status and who proposed them', async () => {
    setup({
      papers: [paper()],
      questions: [
        q({
          tags: [
            {
              node_id: 'gs2.polity',
              title: 'Constitution and Polity',
              status: 'accepted',
              source: 'owner'
            }
          ]
        })
      ]
    })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 1/i }))
    const list = await screen.findByRole('list', { name: /syllabus tags/i })
    expect(within(list).getByText('Constitution and Polity')).toBeInTheDocument()
    expect(within(list).getByText(/accepted/i)).toBeInTheDocument()
    expect(within(list).getByText(/you added this/i)).toBeInTheDocument()
  })

  it('suggests tags, labelled as suggestions, and the owner accepts or rejects them', async () => {
    const api = setup({ papers: [paper()] })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 1/i }))
    await userEvent.click(await screen.findByRole('button', { name: /suggest tags/i }))
    const list = await screen.findByRole('list', { name: /syllabus tags/i })
    expect(within(list).getByText(/suggested by ai/i)).toBeInTheDocument()
    await userEvent.click(
      within(list).getByRole('button', { name: /accept constitution and polity/i })
    )
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/pyq/questions/PRE-2023-GS1-001/tags/gs2.polity',
        body: { decision: 'accept' }
      })
    )
    expect(await within(list).findByText(/^accepted/i)).toBeInTheDocument()
    await userEvent.click(
      within(list).getByRole('button', { name: /reject constitution and polity/i })
    )
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith(expect.objectContaining({ body: { decision: 'reject' } }))
    )
  })

  it('lets the owner add a syllabus node by hand', async () => {
    const api = setup({ papers: [paper()] })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 1/i }))
    await userEvent.selectOptions(
      await screen.findByRole('combobox', { name: /add syllabus node/i }),
      'gs2.polity'
    )
    await userEvent.click(screen.getByRole('button', { name: /add tag/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'POST',
        path: '/pyq/questions/PRE-2023-GS1-001/tags',
        body: { node_id: 'gs2.polity' }
      })
    )
  })

  it('cannot suggest tags for a question without text', async () => {
    setup({ papers: [paper()] })
    render(<PyqScreen />)
    await userEvent.click(
      await screen.findByRole('button', { name: /review prelims 2023 gs-paper-1/i })
    )
    await userEvent.click(await screen.findByRole('button', { name: /open question 2/i }))
    expect(await screen.findByRole('button', { name: /suggest tags/i })).toBeDisabled()
  })
})
