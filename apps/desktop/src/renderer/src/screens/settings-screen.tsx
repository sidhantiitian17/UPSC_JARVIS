import { useCallback, useEffect, useState } from 'react'
import type { components } from '@jarvis/shared'
import { ApiError, getSettings, putSettings, testAi } from '../api/client'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'
import { PrivacyPanel } from '../privacy/privacy-panel'

type SettingsOut = components['schemas']['SettingsOut']
type ProviderInfo = components['schemas']['ProviderInfo']
type AiTestOut = components['schemas']['AiTestOut']

function describeError(e: unknown): string {
  const msg = e instanceof Error ? e.message : String(e)
  if (msg.includes('encryption-unavailable'))
    return 'Could not save the key: your system’s secure storage (encryption) is unavailable, so nothing was stored.'
  return `Something went wrong: ${msg}`
}

function providerStatus(p: ProviderInfo): string {
  if (!p.enabled) return 'Disabled (one-time credit providers are off by default)'
  if (p.needs_key) return p.key_set ? 'Key saved' : 'Needs API key'
  return 'Ready (no key needed)'
}

function ProviderRow({
  p,
  onChanged,
  onError
}: {
  p: ProviderInfo
  onChanged: () => void
  onError: (m: string) => void
}): React.JSX.Element {
  const [value, setValue] = useState('')
  const canEdit = p.enabled && p.needs_key && p.secret_name
  const save = async (): Promise<void> => {
    try {
      await window.jarvis.secrets.set(p.secret_name as string, value)
      setValue('')
      onChanged()
    } catch (e) {
      onError(describeError(e))
    }
  }
  const remove = async (): Promise<void> => {
    try {
      await window.jarvis.secrets.delete(p.secret_name as string)
      onChanged()
    } catch (e) {
      onError(describeError(e))
    }
  }
  return (
    <li className="flex flex-col gap-2 border-b border-line py-3 last:border-0">
      <div className="flex items-baseline justify-between gap-4">
        <span className="font-semibold">{p.name}</span>
        <span className="text-sm text-muted">
          {p.kind.replace('_', ' ')} · {providerStatus(p)}
        </span>
      </div>
      {canEdit && (
        <div className="flex gap-2">
          <input
            type="password"
            autoComplete="off"
            aria-label={`${p.name} API key`}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={p.key_set ? '•••••••• (saved)' : 'Paste your API key'}
            className="min-h-10 flex-1 rounded-lg border border-line bg-app-bg px-3 text-sm"
          />
          <Button disabled={value.length === 0} onClick={save} aria-label={`Save ${p.name} key`}>
            Save
          </Button>
          {p.key_set && (
            <Button variant="ghost" onClick={remove} aria-label={`Remove ${p.name} key`}>
              Remove
            </Button>
          )}
        </div>
      )}
    </li>
  )
}

function TimerCard({
  settings,
  onSaved,
  onError
}: {
  settings: SettingsOut
  onSaved: (s: SettingsOut) => void
  onError: (m: string) => void
}): React.JSX.Element {
  const [focus, setFocus] = useState(String(settings.focus_minutes))
  const [rest, setRest] = useState(String(settings.break_minutes))
  const save = async (): Promise<void> => {
    try {
      onSaved(await putSettings({ focus_minutes: Number(focus), break_minutes: Number(rest) }))
    } catch (e) {
      onError(
        e instanceof ApiError && e.status === 422
          ? 'Focus must be 5–180 minutes and break 1–60 minutes.'
          : describeError(e)
      )
    }
  }
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold">Focus timer</h2>
      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Focus minutes
          <input
            type="number"
            min={5}
            max={180}
            aria-label="Focus minutes"
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            className="min-h-10 w-28 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Break minutes
          <input
            type="number"
            min={1}
            max={60}
            aria-label="Break minutes"
            value={rest}
            onChange={(e) => setRest(e.target.value)}
            className="min-h-10 w-28 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <Button onClick={save}>Save timer</Button>
      </div>
    </Card>
  )
}

function ExamCard({
  settings,
  onSaved,
  onError
}: {
  settings: SettingsOut
  onSaved: (s: SettingsOut) => void
  onError: (m: string) => void
}): React.JSX.Element {
  const [target, setTarget] = useState(settings.exam_target)
  const [date, setDate] = useState(settings.exam_date ?? '')
  const saveDate = async (): Promise<void> => {
    try {
      onSaved(await putSettings({ exam_date: date }))
    } catch (e) {
      onError(
        e instanceof ApiError && e.status === 422 ? 'Enter a valid exam date.' : describeError(e)
      )
    }
  }
  const save = async (): Promise<void> => {
    try {
      onSaved(await putSettings({ exam_target: target.trim() }))
    } catch (e) {
      onError(
        e instanceof ApiError && e.status === 422
          ? 'The exam target must be 1 to 60 characters.'
          : describeError(e)
      )
    }
  }
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold">Exam target</h2>
      <p className="text-sm text-muted">
        Shown to the AI as part of your profile so feedback fits your timeline.
      </p>
      <div className="flex items-end gap-4">
        <input
          type="text"
          aria-label="Exam target"
          maxLength={60}
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          className="min-h-10 w-64 rounded-lg border border-line bg-app-bg px-3"
        />
        <Button onClick={save} aria-label="Save exam target">
          Save
        </Button>
      </div>
      <div className="flex items-end gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Exam date
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="min-h-10 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <Button onClick={saveDate} aria-label="Save exam date">
          Save
        </Button>
      </div>
      {!settings.exam_date && (
        <p className="text-xs text-muted">
          No date set yet: forecasts use an assumed date in 2028.
        </p>
      )}
    </Card>
  )
}

function GoalsCard({
  settings,
  onSaved,
  onError
}: {
  settings: SettingsOut
  onSaved: (s: SettingsOut) => void
  onError: (m: string) => void
}): React.JSX.Element {
  const [goal, setGoal] = useState(String(settings.daily_goal_minutes))
  const [bad, setBad] = useState(String(settings.bad_day_goal_minutes))
  const save = async (): Promise<void> => {
    try {
      onSaved(
        await putSettings({ daily_goal_minutes: Number(goal), bad_day_goal_minutes: Number(bad) })
      )
    } catch (e) {
      onError(
        e instanceof ApiError && e.status === 422
          ? 'Daily goal must be 10–600 minutes and the bad-day goal 5–300 minutes.'
          : describeError(e)
      )
    }
  }
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold">Daily goals</h2>
      <p className="text-sm text-muted">
        A day counts for your streak when this many minutes passed the recall gate. On a bad day the
        smaller goal applies.
      </p>
      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Daily goal (verified min)
          <input
            type="number"
            min={10}
            max={600}
            aria-label="Daily goal minutes"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            className="min-h-10 w-28 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Bad-day goal (verified min)
          <input
            type="number"
            min={5}
            max={300}
            aria-label="Bad-day goal minutes"
            value={bad}
            onChange={(e) => setBad(e.target.value)}
            className="min-h-10 w-28 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <Button onClick={save} aria-label="Save goals">
          Save
        </Button>
      </div>
    </Card>
  )
}

function SleepCard({
  settings,
  onSaved,
  onError
}: {
  settings: SettingsOut
  onSaved: (s: SettingsOut) => void
  onError: (m: string) => void
}): React.JSX.Element {
  const [enabled, setEnabled] = useState(settings.sleep_guard_enabled)
  const [start, setStart] = useState(settings.sleep_start)
  const [end, setEnd] = useState(settings.sleep_end)
  const save = async (): Promise<void> => {
    try {
      onSaved(
        await putSettings({ sleep_guard_enabled: enabled, sleep_start: start, sleep_end: end })
      )
    } catch (e) {
      onError(describeError(e))
    }
  }
  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold">Sleep guard</h2>
      <p className="text-sm text-muted">
        During this window Today shows a gentle note that sleep helps memory. Nothing is ever
        locked.
      </p>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => setEnabled(e.target.checked)}
          aria-label="Sleep guard"
        />
        Remind me to sleep
      </label>
      <div className="flex flex-wrap items-end gap-4">
        <label className="flex flex-col gap-1 text-sm">
          Sleep starts
          <input
            type="time"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="min-h-10 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Sleep ends
          <input
            type="time"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="min-h-10 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <Button onClick={save} aria-label="Save sleep guard">
          Save
        </Button>
      </div>
    </Card>
  )
}

export function SettingsScreen(): React.JSX.Element {
  const [settings, setSettings] = useState<SettingsOut | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [ai, setAi] = useState<AiTestOut | null>(null)
  const [testing, setTesting] = useState(false)

  const [reloads, setReloads] = useState(0)
  const load = useCallback((): void => setReloads((n) => n + 1), [])

  useEffect(() => {
    let alive = true
    getSettings()
      .then((s) => alive && setSettings(s))
      .catch((e) => alive && setError(describeError(e)))
    return () => {
      alive = false
    }
  }, [reloads])

  const chooseFolder = async (key: 'library_path' | 'vault_path'): Promise<void> => {
    try {
      const picked = await window.jarvis.pickFolder()
      if (!picked) return
      setSettings(await putSettings({ [key]: picked }))
    } catch (e) {
      setError(describeError(e))
    }
  }

  const runTest = async (): Promise<void> => {
    setTesting(true)
    setAi(null)
    try {
      setAi(await testAi())
    } catch (e) {
      setAi({ ok: false, error: describeError(e) })
    } finally {
      setTesting(false)
    }
  }

  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-muted">
          Folders, free AI providers and privacy. Keys are stored encrypted on this PC.
        </p>
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-danger p-3 text-sm text-danger">
          {error}
        </div>
      )}

      <Card className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold">Folders</h2>
        {(
          [
            ['library_path', 'Library folder', 'library'],
            ['vault_path', 'Vault folder', 'vault']
          ] as const
        ).map(([key, label, short]) => (
          <div key={key} className="flex items-center justify-between gap-4">
            <div>
              <div className="text-sm text-muted">{label}</div>
              {settings?.[key] ? (
                <code className="text-sm">{settings[key]}</code>
              ) : (
                <span className="text-sm">Not chosen</span>
              )}
            </div>
            <Button onClick={() => chooseFolder(key)} aria-label={`Choose ${short} folder`}>
              Choose folder
            </Button>
          </div>
        ))}
      </Card>

      {settings && (
        <ExamCard
          key={settings.exam_target}
          settings={settings}
          onSaved={setSettings}
          onError={setError}
        />
      )}

      {settings && (
        <SleepCard
          key={`${settings.sleep_guard_enabled}-${settings.sleep_start}-${settings.sleep_end}`}
          settings={settings}
          onSaved={setSettings}
          onError={setError}
        />
      )}

      {settings && (
        <GoalsCard
          key={`${settings.daily_goal_minutes}-${settings.bad_day_goal_minutes}`}
          settings={settings}
          onSaved={setSettings}
          onError={setError}
        />
      )}

      {settings && (
        <TimerCard
          key={`${settings.focus_minutes}-${settings.break_minutes}`}
          settings={settings}
          onSaved={setSettings}
          onError={setError}
        />
      )}

      <Card>
        <h2 className="mb-2 text-xl font-semibold">AI providers</h2>
        <ul aria-label="AI providers">
          {settings?.providers.map((p) => (
            <ProviderRow key={p.name} p={p} onChanged={load} onError={setError} />
          ))}
        </ul>
        <div className="mt-4 flex items-center gap-4">
          <Button variant="primary" onClick={runTest} disabled={testing}>
            Test AI
          </Button>
          {ai && (
            <p role="status" className={ai.ok ? 'text-sm text-success' : 'text-sm text-danger'}>
              {ai.ok
                ? `AI reachable via ${ai.provider} (${ai.model}): ${ai.text}`
                : (ai.error ?? 'Test failed')}
            </p>
          )}
        </div>
      </Card>

      <PrivacyPanel />
    </section>
  )
}
