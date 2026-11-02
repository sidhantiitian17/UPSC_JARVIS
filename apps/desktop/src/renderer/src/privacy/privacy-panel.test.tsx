import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { PrivacyPanel } from './privacy-panel'

const cat = (id: string, title: string, count: number, warning = 'Be careful.'): object => ({
  id,
  title,
  description: `${title} description`,
  warning,
  count,
  where: 'The database file in your JARVIS data folder (this PC only).',
  retention: 'Kept until you delete it.'
})
const SUMMARY = {
  categories: [
    cat(
      'library',
      'Library text',
      3,
      'Deleting this also removes the sessions tied to those books.'
    ),
    cat('study_history', 'Study history', 12),
    cat('review', 'Review cards', 40),
    cat('ai_cache', 'AI cache and usage log', 100)
  ],
  locations: {
    data_dir: 'C:\\Users\\me\\AppData\\Roaming\\jarvis',
    vault_path: 'D:\\Vault',
    library_path: null
  },
  notes: [
    'API keys are stored encrypted by your operating system on this PC only.',
    'Nothing leaves this PC except the AI requests you trigger.'
  ]
}

function setup(): ReturnType<typeof vi.fn> {
  let current = SUMMARY
  const api = vi.fn(async (req: { method: string; path: string }) => {
    if (req.method === 'GET' && req.path === '/privacy/summary')
      return { status: 200, body: current }
    if (req.method === 'DELETE' && req.path.startsWith('/privacy/')) {
      const id = req.path.split('/')[2].split('?')[0]
      current = {
        ...current,
        categories: current.categories.map((c) =>
          (c as { id: string }).id === id ? { ...(c as object), count: 0 } : c
        )
      }
      return { status: 200, body: current }
    }
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

describe('PrivacyPanel', () => {
  it('lists each category with its count, location and retention', async () => {
    setup()
    render(<PrivacyPanel />)
    const list = await screen.findByRole('list', { name: /stored data/i })
    expect(within(list).getAllByRole('listitem')).toHaveLength(4)
    expect(within(list).getByText('Study history')).toBeInTheDocument()
    expect(within(list).getByText(/12 items/i)).toBeInTheDocument()
    expect(within(list).getAllByText(/kept until you delete it/i)).toHaveLength(4)
  })

  it('shows where things live and the privacy notes', async () => {
    setup()
    render(<PrivacyPanel />)
    expect(await screen.findByText(/C:\\Users\\me\\AppData\\Roaming\\jarvis/)).toBeInTheDocument()
    expect(screen.getByText(/D:\\Vault/)).toBeInTheDocument()
    expect(screen.getByText(/encrypted by your operating system/i)).toBeInTheDocument()
    expect(screen.getByText(/nothing leaves this pc/i)).toBeInTheDocument()
  })

  it('asks for confirmation, with the warning, before deleting', async () => {
    const api = setup()
    render(<PrivacyPanel />)
    await userEvent.click(await screen.findByRole('button', { name: /delete library text/i }))
    const confirm = await screen.findByRole('alertdialog')
    expect(confirm).toHaveTextContent(/sessions tied to those books/i)
    expect(api).not.toHaveBeenCalledWith(expect.objectContaining({ method: 'DELETE' }))
    await userEvent.click(within(confirm).getByRole('button', { name: /keep my data/i }))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(api).not.toHaveBeenCalledWith(expect.objectContaining({ method: 'DELETE' }))
  })

  it('deletes a category after confirmation and refreshes the count', async () => {
    const api = setup()
    render(<PrivacyPanel />)
    await userEvent.click(await screen.findByRole('button', { name: /delete review cards/i }))
    await userEvent.click(
      within(await screen.findByRole('alertdialog')).getByRole('button', {
        name: /delete permanently/i
      })
    )
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'DELETE',
        path: '/privacy/review?confirm=yes',
        body: undefined
      })
    )
    expect(await screen.findByText(/^0 items/)).toBeInTheDocument()
  })

  it('never offers a primary delete button', async () => {
    setup()
    render(<PrivacyPanel />)
    await screen.findByRole('list', { name: /stored data/i })
    expect(
      screen.getAllByRole('button').filter((b) => b.getAttribute('data-variant') === 'primary')
    ).toHaveLength(0)
  })

  it('shows a friendly error when the summary cannot load', async () => {
    ;(window as unknown as { jarvis: unknown }).jarvis = {
      platform: 'test',
      api: vi.fn(async () => ({ status: 500, body: null })),
      status: async () => ({ ready: true })
    }
    render(<PrivacyPanel />)
    expect(await screen.findByRole('alert')).toHaveTextContent(/could not load/i)
  })
})
