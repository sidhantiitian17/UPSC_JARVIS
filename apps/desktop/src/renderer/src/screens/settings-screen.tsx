import { useCallback, useEffect, useState } from 'react'
import type { components } from '@jarvis/shared'
import { getSettings, putSettings, testAi } from '../api/client'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'

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
    </section>
  )
}
