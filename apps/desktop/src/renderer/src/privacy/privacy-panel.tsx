import { useEffect, useState } from 'react'
import { deletePrivacyCategory, getPrivacy, type PrivacySummary } from '../api/client'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'

export function PrivacyPanel(): React.JSX.Element {
  const [data, setData] = useState<PrivacySummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<PrivacySummary['categories'][number] | null>(null)

  useEffect(() => {
    let alive = true
    getPrivacy()
      .then((d) => alive && setData(d))
      .catch(
        () => alive && setError('Could not load the privacy summary. Is the local service running?')
      )
    return () => {
      alive = false
    }
  }, [])

  const confirmDelete = async (): Promise<void> => {
    if (!pending) return
    const id = pending.id
    setPending(null)
    try {
      setData(await deletePrivacyCategory(id))
    } catch {
      setError('Could not delete that data. Nothing was changed.')
    }
  }

  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold">Privacy: what is stored</h2>
      {error && (
        <div role="alert" className="rounded-lg border border-danger p-2 text-sm text-danger">
          {error}
        </div>
      )}
      {data && (
        <>
          <ul aria-label="Stored data" className="flex flex-col">
            {data.categories.map((c) => (
              <li
                key={c.id}
                className="flex items-start justify-between gap-4 border-b border-line py-3 last:border-0"
              >
                <div className="flex flex-col gap-1">
                  <span className="font-semibold">{c.title}</span>
                  <span className="text-sm text-muted">{c.description}</span>
                  <span className="text-xs text-muted">
                    {c.count} items · {c.where} {c.retention}
                  </span>
                </div>
                <Button
                  aria-label={`Delete ${c.title}`}
                  disabled={c.count === 0}
                  onClick={() => setPending(c)}
                >
                  Delete
                </Button>
              </li>
            ))}
          </ul>
          <dl className="grid grid-cols-[8rem_1fr] gap-1 text-sm">
            <dt className="text-muted">Data folder</dt>
            <dd>
              <code>{data.locations.data_dir ?? 'in memory only'}</code>
            </dd>
            <dt className="text-muted">Vault folder</dt>
            <dd>
              <code>{data.locations.vault_path ?? 'not set'}</code>
            </dd>
            <dt className="text-muted">Library folder</dt>
            <dd>
              <code>{data.locations.library_path ?? 'not set'}</code>
            </dd>
          </dl>
          <ul className="list-disc pl-5 text-sm text-muted">
            {data.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </>
      )}

      {pending && (
        <div
          role="alertdialog"
          aria-label={`Delete ${pending.title}?`}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-6"
        >
          <div className="flex max-w-md flex-col gap-4 rounded-card bg-surface p-6">
            <p className="font-semibold">
              Delete {pending.title}? {pending.count} items will be removed.
            </p>
            <p>{pending.warning}</p>
            <div className="flex gap-2">
              <Button onClick={() => void confirmDelete()}>Delete permanently</Button>
              <Button onClick={() => setPending(null)}>Keep my data</Button>
            </div>
          </div>
        </div>
      )}
    </Card>
  )
}
