import { useEffect, useState } from 'react'
import {
  ApiError,
  addPyqTag,
  decidePyqTag,
  getSyllabusTree,
  suggestPyqTags,
  type PyqQuestion,
  type PyqTag,
  type SyllabusNode
} from '../api/client'
import { Button } from '../components/ui/button'

const leaves = (nodes: SyllabusNode[]): SyllabusNode[] =>
  nodes.flatMap((n) => (n.children.length ? leaves(n.children) : [n]))

const SOURCE_LABEL: Record<string, string> = {
  llm: 'suggested by AI',
  keyword: 'suggested by keyword match',
  owner: 'you added this'
}

function messageOf(e: unknown): string {
  if (e instanceof ApiError) {
    const d = (e.body as { detail?: unknown } | null)?.detail
    if (typeof d === 'string') return d
  }
  return 'Something went wrong. Is the local service running?'
}

/** Syllabus tags for one PYQ. A suggestion counts only after the owner accepts it. */
export function TagPanel({ q }: { q: PyqQuestion }): React.JSX.Element {
  const [tags, setTags] = useState<PyqTag[]>(q.tags ?? [])
  const [nodes, setNodes] = useState<SyllabusNode[]>([])
  const [pick, setPick] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let alive = true
    getSyllabusTree()
      .then((t) => alive && setNodes(leaves(t)))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])

  const run = async (fn: () => Promise<PyqTag[]>): Promise<void> => {
    setBusy(true)
    setError(null)
    try {
      setTags(await fn())
    } catch (e) {
      setError(messageOf(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section aria-label="Syllabus tags" className="flex flex-col gap-2">
      <div className="flex items-center gap-3">
        <h3 className="text-sm font-semibold">Syllabus tags</h3>
        <Button
          disabled={busy || !q.stem.trim()}
          onClick={() => void run(() => suggestPyqTags(q.id))}
        >
          Suggest tags
        </Button>
      </div>
      {error && (
        <div role="alert" className="rounded-lg border border-danger p-2 text-sm text-danger">
          {error}
        </div>
      )}
      <ul aria-label="Syllabus tags" className="flex flex-col gap-1">
        {tags.map((t) => (
          <li key={t.node_id} className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium">{t.title}</span>
            <span className="rounded border border-line px-1.5 text-xs">
              {t.status === 'suggested'
                ? 'Suggested'
                : t.status === 'accepted'
                  ? 'Accepted'
                  : 'Rejected'}
            </span>
            <span className="text-xs text-muted">{SOURCE_LABEL[t.source] ?? t.source}</span>
            {t.status !== 'accepted' && (
              <Button
                aria-label={`Accept ${t.title}`}
                disabled={busy}
                onClick={() => void run(() => decidePyqTag(q.id, t.node_id, 'accept'))}
              >
                Accept
              </Button>
            )}
            {t.status !== 'rejected' && (
              <Button
                aria-label={`Reject ${t.title}`}
                disabled={busy}
                onClick={() => void run(() => decidePyqTag(q.id, t.node_id, 'reject'))}
              >
                Reject
              </Button>
            )}
          </li>
        ))}
        {tags.length === 0 && <li className="text-sm text-muted">No tags yet.</li>}
      </ul>
      <div className="flex items-end gap-2">
        <label className="flex flex-col gap-1 text-sm">
          Add syllabus node
          <select
            aria-label="Add syllabus node"
            value={pick}
            onChange={(e) => setPick(e.target.value)}
            className="min-h-10 max-w-sm rounded-lg border border-line bg-app-bg px-2"
          >
            <option value="">Choose a node…</option>
            {nodes.map((n) => (
              <option key={n.id} value={n.id}>
                {n.title.length > 70 ? `${n.title.slice(0, 70)}…` : n.title}
              </option>
            ))}
          </select>
        </label>
        <Button
          disabled={!pick || busy}
          onClick={() => void run(() => addPyqTag(q.id, pick)).then(() => setPick(''))}
        >
          Add tag
        </Button>
      </div>
    </section>
  )
}
