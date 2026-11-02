import { useCallback, useEffect, useState } from 'react'
import {
  ApiError,
  getPyqPapers,
  getPyqQuestions,
  importPyq,
  savePyq,
  verifyPyq,
  type PyqPaper,
  type PyqQuestion
} from '../api/client'
import { EmptyState } from '../components/empty-state'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'
import { SCREEN_META } from '../screens'

const STATUS_LABEL: Record<string, string> = {
  parsed: 'Parsed',
  failed: 'Failed',
  reviewed: 'Reviewed',
  verified: 'Verified'
}
const paperLabel = (p: { phase: string; year: number; paper: string }): string =>
  `${p.phase.charAt(0).toUpperCase()}${p.phase.slice(1)} ${p.year} ${p.paper}`

function serverMessage(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    const d = (e.body as { detail?: unknown } | null)?.detail
    if (typeof d === 'string') return d
  }
  return fallback
}

function Editor({
  q,
  onBack,
  onChanged
}: {
  q: PyqQuestion
  onBack: () => void
  onChanged: (q: PyqQuestion) => void
}): React.JSX.Element {
  const [stem, setStem] = useState(q.stem)
  const [options, setOptions] = useState<string[]>(
    q.options.length === 4 ? q.options : ['', '', '', '']
  )
  const [answer, setAnswer] = useState(q.answer ?? '')
  const [error, setError] = useState<string | null>(null)
  const [note, setNote] = useState<string | null>(null)

  const save = async (): Promise<PyqQuestion | null> => {
    try {
      const saved = await savePyq(q.id, { stem, options, answer })
      onChanged(saved)
      setError(null)
      setNote('Saved.')
      return saved
    } catch (e) {
      setError(serverMessage(e, 'Could not save. Is the local service running?'))
      return null
    }
  }
  const verify = async (): Promise<void> => {
    if (!(await save())) return
    try {
      onChanged(await verifyPyq(q.id))
      setNote('Marked verified.')
    } catch (e) {
      setNote(null)
      setError(serverMessage(e, 'Could not verify.'))
    }
  }

  return (
    <section className="flex flex-col gap-4">
      <header className="flex items-center gap-3">
        <Button onClick={onBack}>Back to questions</Button>
        <h2 className="text-xl font-semibold">
          {paperLabel(q)} · Q{q.number} · {STATUS_LABEL[q.status] ?? q.status}
        </h2>
      </header>
      {error && (
        <div role="alert" className="rounded-lg border border-danger p-2 text-sm text-danger">
          {error}
        </div>
      )}
      {note && (
        <p role="status" className="text-sm text-muted">
          {note}
        </p>
      )}
      {q.raw_text && (
        <div>
          <p className="text-sm font-semibold">Raw text from the PDF (read-only)</p>
          <pre className="whitespace-pre-wrap rounded-lg border border-line p-2 text-sm text-muted">
            {q.raw_text}
          </pre>
        </div>
      )}
      <label className="flex flex-col gap-1 text-sm">
        Question text
        <textarea
          aria-label="Question text"
          value={stem}
          onChange={(e) => setStem(e.target.value)}
          rows={6}
          className="rounded-lg border border-line bg-app-bg p-2"
        />
      </label>
      {options.map((o, i) => (
        <label key={i} className="flex flex-col gap-1 text-sm">
          Option {String.fromCharCode(97 + i)}
          <input
            aria-label={`Option ${String.fromCharCode(97 + i)}`}
            value={o}
            onChange={(e) => setOptions(options.map((x, j) => (j === i ? e.target.value : x)))}
            className="min-h-10 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
      ))}
      <label className="flex flex-col gap-1 text-sm">
        Answer
        <select
          aria-label="Answer"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          className="min-h-10 w-40 rounded-lg border border-line bg-app-bg px-3"
        >
          <option value="">Unknown</option>
          {['a', 'b', 'c', 'd'].map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </label>
      <p className="text-xs text-muted">
        An answer is stored only from the official key or from you. No AI ever fills it.
        {q.answer_source !== 'none' && ` Current source: ${q.answer_source}.`}
      </p>
      <p className="text-xs text-muted">Source: {q.source_url ?? 'unknown'}</p>
      <div className="flex gap-2">
        <Button variant="primary" onClick={() => void save()}>
          Save
        </Button>
        <Button onClick={() => void verify()}>Mark verified</Button>
      </div>
    </section>
  )
}

export function PyqScreen(): React.JSX.Element {
  const m = SCREEN_META.pyq
  const [papers, setPapers] = useState<PyqPaper[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [open, setOpen] = useState<PyqPaper | null>(null)
  const [status, setStatus] = useState('')
  const [questions, setQuestions] = useState<PyqQuestion[]>([])
  const [editing, setEditing] = useState<PyqQuestion | null>(null)
  const [reloads, setReloads] = useState(0)

  useEffect(() => {
    let alive = true
    getPyqPapers()
      .then((p) => alive && setPapers(p))
      .catch(
        () => alive && setError('Could not load the PYQ corpus. Is the local service running?')
      )
    return () => {
      alive = false
    }
  }, [reloads])

  useEffect(() => {
    if (!open) return
    let alive = true
    getPyqQuestions(open.phase, open.year, open.paper, status || undefined)
      .then((qs) => alive && setQuestions(qs))
      .catch(() => alive && setError('Could not load the questions.'))
    return () => {
      alive = false
    }
  }, [open, status, reloads])

  const runImport = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const r = await importPyq()
      setNotice(
        `Imported ${r.questions} questions from ${r.files} files (${r.kept_owner_edits} of yours kept as they were).`
      )
      setReloads((n) => n + 1)
    } catch (e) {
      setError(serverMessage(e, 'Import failed.'))
    } finally {
      setBusy(false)
    }
  }, [])

  if (editing)
    return (
      <Editor
        key={editing.id}
        q={editing}
        onBack={() => {
          setEditing(null)
          setReloads((n) => n + 1)
        }}
        onChanged={setEditing}
      />
    )

  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{m.label}</h1>
          <p className="mt-1 text-muted">{m.description}</p>
        </div>
        {papers && papers.length > 0 && !open && (
          <Button onClick={() => void runImport()} disabled={busy}>
            Import dataset
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

      {papers && papers.length === 0 && (
        <EmptyState
          title={m.emptyTitle}
          body={m.emptyBody}
          action={
            <Button variant="primary" onClick={() => void runImport()} disabled={busy}>
              {m.primaryAction}
            </Button>
          }
        />
      )}

      {papers && papers.length > 0 && !open && (
        <Card>
          <ul className="flex flex-col">
            {papers.map((p) => (
              <li
                key={`${p.phase}-${p.year}-${p.paper}`}
                aria-label={paperLabel(p)}
                className="flex items-center justify-between gap-4 border-b border-line py-3 last:border-0"
              >
                <div>
                  <span className="font-semibold">{paperLabel(p)}</span>
                  <span className="ml-3 text-sm text-muted">
                    {p.parsed} parsed · {p.failed} failed · {p.reviewed} reviewed · {p.verified}{' '}
                    verified
                  </span>
                </div>
                <Button aria-label={`Review ${paperLabel(p)}`} onClick={() => setOpen(p)}>
                  Review
                </Button>
              </li>
            ))}
          </ul>
        </Card>
      )}

      {open && (
        <Card className="flex flex-col gap-3">
          <div className="flex items-center gap-3">
            <Button onClick={() => setOpen(null)}>Back to papers</Button>
            <h2 className="text-xl font-semibold">{paperLabel(open)}</h2>
            <label className="ml-auto flex items-center gap-2 text-sm">
              Status
              <select
                aria-label="Status"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="min-h-10 rounded-lg border border-line bg-app-bg px-2"
              >
                <option value="">All</option>
                {Object.entries(STATUS_LABEL).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <ul className="flex flex-col">
            {questions.map((q) => (
              <li
                key={q.id}
                className="flex items-center justify-between gap-4 border-b border-line py-2 last:border-0"
              >
                <div className="min-w-0">
                  <span className="font-semibold">Q{q.number}</span>
                  <span className="ml-2 rounded border border-line px-1.5 text-xs">
                    {STATUS_LABEL[q.status] ?? q.status}
                  </span>
                  <p className="truncate text-sm text-muted">
                    {q.stem || '(text not parsed: open to fix it)'}
                  </p>
                </div>
                <Button aria-label={`Open question ${q.number}`} onClick={() => setEditing(q)}>
                  Open
                </Button>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </section>
  )
}
