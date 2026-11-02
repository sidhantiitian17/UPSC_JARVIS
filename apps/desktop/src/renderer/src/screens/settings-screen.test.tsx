import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi, type Mock } from 'vitest'
import { SettingsScreen } from './settings-screen'

type Provider = {
  name: string
  kind: string
  enabled: boolean
  needs_key: boolean
  key_set: boolean
  secret_name: string | null
}

const providers: Provider[] = [
  {
    name: 'ollama',
    kind: 'local',
    enabled: true,
    needs_key: false,
    key_set: false,
    secret_name: null
  },
  {
    name: 'gemini',
    kind: 'recurring_free',
    enabled: true,
    needs_key: true,
    key_set: false,
    secret_name: 'gemini_key'
  },
  {
    name: 'credit-co',
    kind: 'one_time_credit',
    enabled: false,
    needs_key: true,
    key_set: false,
    secret_name: 'credit_key'
  }
]

function setup(opts: { aiResult?: unknown; secretsError?: string; picked?: string | null } = {}): {
  api: Mock
  secrets: { set: Mock; delete: Mock; names: Mock }
  pickFolder: Mock
} {
  let settings = {
    library_path: null as string | null,
    vault_path: null as string | null,
    focus_minutes: 50,
    break_minutes: 10,
    review_daily_limit: 40,
    exam_target: 'Prelims 2028',
    exam_date: null,
    pet_mode: 'coach',
    focus_guard_enabled: false,
    sleep_guard_enabled: true,
    sleep_start: '23:30',
    sleep_end: '05:30',
    daily_goal_minutes: 60,
    bad_day_goal_minutes: 20,
    providers,
    db_version: 2
  }
  const api = vi.fn(async (req: { method: string; path: string; body?: unknown }) => {
    if (req.method === 'GET' && req.path === '/privacy/summary')
      return {
        status: 200,
        body: {
          categories: [],
          locations: { data_dir: null, vault_path: null, library_path: null },
          notes: []
        }
      }
    if (req.method === 'GET' && req.path === '/settings') return { status: 200, body: settings }
    if (req.method === 'PUT' && req.path === '/settings') {
      settings = { ...settings, ...(req.body as object) }
      return { status: 200, body: settings }
    }
    if (req.method === 'POST' && req.path === '/llm/test')
      return {
        status: 200,
        body: opts.aiResult ?? { ok: true, provider: 'ollama', model: 'm', text: 'pong' }
      }
    return { status: 404, body: null }
  })
  const secrets = {
    set: vi.fn(async () => {
      if (opts.secretsError) throw new Error(opts.secretsError)
      settings = {
        ...settings,
        providers: providers.map((p) => (p.name === 'gemini' ? { ...p, key_set: true } : p))
      }
    }),
    delete: vi.fn(async () => {}),
    names: vi.fn(async () => [])
  }
  const pickFolder = vi.fn(async () => (opts.picked === undefined ? '/data/library' : opts.picked))
  ;(window as unknown as { jarvis: unknown }).jarvis = {
    platform: 'test',
    api,
    status: async () => ({ ready: true }),
    secrets,
    pickFolder
  }
  return { api, secrets, pickFolder }
}

afterEach(() => {
  delete (window as unknown as { jarvis?: unknown }).jarvis
})

describe('Settings screen', () => {
  it('lists providers with an honest status for each', async () => {
    setup()
    render(<SettingsScreen />)
    const list = await screen.findByRole('list', { name: /ai providers/i })
    const items = within(list).getAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(items[0]).toHaveTextContent(/ollama/i)
    expect(items[0]).toHaveTextContent(/no key needed/i)
    expect(items[1]).toHaveTextContent(/needs api key/i)
    expect(items[2]).toHaveTextContent(/disabled/i)
  })

  it('saves a key through the main process and never displays it', async () => {
    const { secrets } = setup()
    render(<SettingsScreen />)
    const input = await screen.findByLabelText(/gemini api key/i)
    expect(input).toHaveAttribute('type', 'password')
    await userEvent.type(input, 'AIza-VERY-SECRET')
    await userEvent.click(screen.getByRole('button', { name: /save gemini/i }))
    await waitFor(() => expect(secrets.set).toHaveBeenCalledWith('gemini_key', 'AIza-VERY-SECRET'))
    await waitFor(() => expect(screen.getByLabelText(/gemini api key/i)).toHaveValue(''))
    expect(document.body.textContent).not.toContain('AIza-VERY-SECRET')
    expect(await screen.findByText(/key saved/i)).toBeInTheDocument()
  })

  it('shows the reason when the OS keystore is unavailable', async () => {
    setup({ secretsError: 'encryption-unavailable' })
    render(<SettingsScreen />)
    await userEvent.type(await screen.findByLabelText(/gemini api key/i), 'k')
    await userEvent.click(screen.getByRole('button', { name: /save gemini/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/encryption/i)
  })

  it('chooses a folder with the native picker and saves it', async () => {
    const { api, pickFolder } = setup()
    render(<SettingsScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /choose library folder/i }))
    await waitFor(() => expect(pickFolder).toHaveBeenCalled())
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { library_path: '/data/library' }
      })
    )
    expect(await screen.findByText('/data/library')).toBeInTheDocument()
  })

  it('does nothing when the folder dialog is cancelled', async () => {
    const { api } = setup({ picked: null })
    render(<SettingsScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /choose vault folder/i }))
    expect(api).not.toHaveBeenCalledWith(expect.objectContaining({ method: 'PUT' }))
  })

  it('Test AI shows the provider and answer, or the failure reason', async () => {
    setup()
    const { unmount } = render(<SettingsScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /test ai/i }))
    expect(await screen.findByText(/reachable via ollama/i)).toBeInTheDocument()
    unmount()
    setup({ aiResult: { ok: false, error: 'all providers failed for ping' } })
    render(<SettingsScreen />)
    await userEvent.click(await screen.findByRole('button', { name: /test ai/i }))
    expect(await screen.findByText(/all providers failed/i)).toBeInTheDocument()
  })

  it('has exactly one primary action', async () => {
    setup()
    render(<SettingsScreen />)
    await screen.findByRole('list', { name: /ai providers/i })
    const primary = screen
      .getAllByRole('button')
      .filter((b) => b.getAttribute('data-variant') === 'primary')
    expect(primary).toHaveLength(1)
  })

  it('shows and saves the focus timer lengths', async () => {
    const { api } = setup()
    render(<SettingsScreen />)
    const focus = await screen.findByRole('spinbutton', { name: /focus minutes/i })
    expect(focus).toHaveValue(50)
    expect(screen.getByRole('spinbutton', { name: /break minutes/i })).toHaveValue(10)
    await userEvent.clear(focus)
    await userEvent.type(focus, '25')
    await userEvent.click(screen.getByRole('button', { name: /save timer/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { focus_minutes: 25, break_minutes: 10 }
      })
    )
  })

  it('shows the exam target (Prelims 2028 by default) and saves a change', async () => {
    const { api } = setup()
    render(<SettingsScreen />)
    const input = await screen.findByRole('textbox', { name: /exam target/i })
    expect(input).toHaveValue('Prelims 2028')
    await userEvent.clear(input)
    await userEvent.type(input, 'Prelims 2029')
    await userEvent.click(screen.getByRole('button', { name: /save exam target/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { exam_target: 'Prelims 2029' }
      })
    )
  })

  it('shows and saves the daily goals that drive streaks', async () => {
    const { api } = setup()
    render(<SettingsScreen />)
    const goal = await screen.findByRole('spinbutton', { name: /daily goal minutes/i })
    expect(goal).toHaveValue(60)
    expect(screen.getByRole('spinbutton', { name: /bad-day goal minutes/i })).toHaveValue(20)
    await userEvent.clear(goal)
    await userEvent.type(goal, '45')
    await userEvent.click(screen.getByRole('button', { name: /save goals/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { daily_goal_minutes: 45, bad_day_goal_minutes: 20 }
      })
    )
  })

  it('shows the sleep window and saves changes', async () => {
    const { api } = setup()
    render(<SettingsScreen />)
    expect(await screen.findByRole('checkbox', { name: /sleep guard/i })).toBeChecked()
    expect(screen.getByLabelText(/sleep starts/i)).toHaveValue('23:30')
    expect(screen.getByLabelText(/sleep ends/i)).toHaveValue('05:30')
    await userEvent.click(screen.getByRole('checkbox', { name: /sleep guard/i }))
    await userEvent.click(screen.getByRole('button', { name: /save sleep guard/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { sleep_guard_enabled: false, sleep_start: '23:30', sleep_end: '05:30' }
      })
    )
  })

  it('saves the exam date', async () => {
    const { api } = setup()
    render(<SettingsScreen />)
    const date = await screen.findByLabelText(/^exam date$/i)
    await userEvent.type(date, '2028-05-28')
    await userEvent.click(screen.getByRole('button', { name: /save exam date/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { exam_date: '2028-05-28' }
      })
    )
  })

  it('shows the pet mode and status, saves a new mode and can say hello', async () => {
    const { api } = setup()
    const pet = {
      event: vi.fn(),
      setMode: vi.fn(async () => undefined),
      status: vi.fn(async () => ({ available: true, mode: 'coach' })),
      test: vi.fn(async () => true)
    }
    ;(window as unknown as { jarvis: { pet: unknown } }).jarvis.pet = pet
    render(<SettingsScreen />)
    expect(await screen.findByText(/pet is connected/i)).toBeInTheDocument()
    const mode = screen.getByRole('combobox', { name: /pet mode/i })
    expect(mode).toHaveValue('coach')
    await userEvent.selectOptions(mode, 'strict')
    await userEvent.click(screen.getByRole('button', { name: /save pet mode/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { pet_mode: 'strict' }
      })
    )
    expect(pet.setMode).toHaveBeenCalledWith('strict')
    await userEvent.click(screen.getByRole('button', { name: /say hello/i }))
    expect(pet.test).toHaveBeenCalled()
  })

  it('explains kindly when OpenPets is not running', async () => {
    setup()
    ;(window as unknown as { jarvis: { pet: unknown } }).jarvis.pet = {
      event: vi.fn(),
      setMode: vi.fn(),
      status: vi.fn(async () => ({ available: false, mode: 'coach' })),
      test: vi.fn(async () => false)
    }
    render(<SettingsScreen />)
    expect(await screen.findByText(/openpets is not running/i)).toBeInTheDocument()
  })

  it('Focus Guard is off by default, explains what it stores, and is switched on with consent', async () => {
    const { api } = setup()
    const setEnabled = vi.fn(async () => undefined)
    ;(window as unknown as { jarvis: { focus: unknown } }).jarvis.focus = {
      setEnabled,
      setSession: vi.fn()
    }
    render(<SettingsScreen />)
    const box = await screen.findByRole('checkbox', { name: /focus guard/i })
    expect(box).not.toBeChecked()
    expect(screen.getByText(/never window titles or web addresses/i)).toBeInTheDocument()
    expect(screen.getByText(/only while a focus block is running/i)).toBeInTheDocument()
    await userEvent.click(box)
    await userEvent.click(screen.getByRole('button', { name: /save focus guard/i }))
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith({
        method: 'PUT',
        path: '/settings',
        body: { focus_guard_enabled: true }
      })
    )
    expect(setEnabled).toHaveBeenCalledWith(true)
  })
})
