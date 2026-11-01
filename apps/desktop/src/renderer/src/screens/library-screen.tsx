import { useCallback, useEffect, useState } from 'react'
import {
  ApiError,
  addDocument,
  listDocuments,
  searchLibrary,
  type LibraryDocument,
  type SearchHit
} from '../api/client'
import { EmptyState } from '../components/empty-state'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'
import { SCREEN_META } from '../screens'

function addError(e: unknown): string {
  if (e instanceof ApiError && e.status === 422) {
    return (e.body as { detail?: string } | null)?.detail ?? 'That file could not be added.'
  }
  return 'Could not add the file. Is the local service running?'
}

export function LibraryScreen(): React.JSX.Element {
  const m = SCREEN_META.study
  const [docs, setDocs] = useState<LibraryDocument[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState<SearchHit[] | null>(null)
  const [reloads, setReloads] = useState(0)

  useEffect(() => {
    let alive = true
    listDocuments()
      .then((d) => alive && setDocs(d))
      .catch(() => alive && setError('Could not load the library. Is the local service running?'))
    return () => {
      alive = false
    }
  }, [reloads])

  const addPath = useCallback(async (path: string): Promise<void> => {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const res = await addDocument(path)
      if (res.duplicate) setNotice(`“${res.title}” is already in your library.`)
      else if (res.warning) setNotice(res.warning)
      else setNotice(`Added “${res.title}” (${res.page_count} pages, ${res.chunks} chunks).`)
      setReloads((n) => n + 1)
    } catch (e) {
      setError(addError(e))
    } finally {
      setBusy(false)
    }
  }, [])

  const pick = async (): Promise<void> => {
    const path = await window.jarvis.pickPdf()
    if (path) await addPath(path)
  }

  const onDrop = async (e: React.DragEvent): Promise<void> => {
    e.preventDefault()
    for (const file of Array.from(e.dataTransfer.files)) {
      const path = window.jarvis.pathForFile(file)
      if (path) await addPath(path)
    }
  }

  const runSearch = async (e: React.FormEvent): Promise<void> => {
    e.preventDefault()
    if (!query.trim()) return setHits(null)
    try {
      setHits(await searchLibrary(query))
    } catch {
      setError('Search failed. Is the local service running?')
    }
  }

  const titleOf = (id: number): string => docs?.find((d) => d.id === id)?.title ?? `Document ${id}`

  return (
    <section
      className="flex max-w-3xl flex-col gap-6"
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
    >
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{m.label}</h1>
          <p className="mt-1 text-muted">{m.description}</p>
        </div>
        {docs && docs.length > 0 && (
          <Button variant="primary" onClick={pick} disabled={busy}>
            Add PDF
          </Button>
        )}
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-danger p-3 text-sm text-danger">
          {error}
        </div>
      )}
      {notice && (
        <p role="status" className="rounded-lg border border-line p-3 text-sm">
          {notice}
        </p>
      )}

      {docs && docs.length === 0 && (
        <EmptyState
          title={m.emptyTitle}
          body={`${m.emptyBody} You can also drop a PDF anywhere on this screen.`}
          action={
            <Button variant="primary" onClick={pick} disabled={busy}>
              Add PDF
            </Button>
          }
        />
      )}

      {docs && docs.length > 0 && (
        <>
          <form onSubmit={runSearch} role="search">
            <input
              type="search"
              aria-label="Search library"
              placeholder="Search all your books…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="min-h-10 w-full rounded-lg border border-line bg-app-bg px-3 text-sm"
            />
          </form>

          {hits && (
            <Card>
              <h2 className="mb-2 text-xl font-semibold">
                {hits.length === 0 ? 'No matches' : `${hits.length} matches`}
              </h2>
              <ul className="flex flex-col gap-3">
                {hits.map((h) => (
                  <li key={h.id} className="border-b border-line pb-3 last:border-0">
                    <div className="text-xs text-muted">
                      <span data-testid="hit-doc">{titleOf(h.document_id)}</span> · page {h.page}
                    </div>
                    <p className="text-sm">{h.text}</p>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card>
            <ul aria-label="Documents" className="flex flex-col">
              {docs.map((d) => (
                <li
                  key={d.id}
                  className="flex items-baseline justify-between gap-4 border-b border-line py-3 last:border-0"
                >
                  <span className="font-semibold">{d.title}</span>
                  <span className="text-sm text-muted">
                    {d.page_count} pages · {d.chunks} chunks
                    {d.scanned && (
                      <span className="ml-2 rounded border border-warning px-1.5 text-xs text-warning">
                        Scanned
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </section>
  )
}
