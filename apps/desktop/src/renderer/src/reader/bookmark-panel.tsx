import { useEffect, useState } from 'react'
import {
  ApiError,
  cancelSession,
  endSession,
  getActiveSession,
  getSyllabusTree,
  listChunks,
  setSessionTags,
  startSession,
  type ChunkInfo,
  type StudySession,
  type SyllabusNode
} from '../api/client'
import { Button } from '../components/ui/button'

function messageOf(e: unknown): string {
  if (e instanceof ApiError) {
    const d = (e.body as { detail?: unknown } | null)?.detail
    if (typeof d === 'string') return d
    if (d && typeof d === 'object' && 'message' in d)
      return String((d as { message: unknown }).message)
  }
  return 'Something went wrong. Is the local service running?'
}

function leaves(nodes: SyllabusNode[]): SyllabusNode[] {
  return nodes.flatMap((n) => (n.children.length ? leaves(n.children) : [n]))
}

const snippet = (t: string): string => (t.length > 140 ? `${t.slice(0, 140)}…` : t)

type Props = {
  documentId: number
  page: number
  /** focused seconds from the timer, sent with the end bookmark */
  focusedSeconds?: number
  onStarted?: () => void
  onEnded?: () => void
  onCancelled?: () => void
  /** true when a session of this document is running (also after an app restart) */
  onActive?: (running: boolean) => void
}

/** Start/end bookmarks for the current page's chunks, plus the saved-session summary. */
export function BookmarkPanel({
  documentId,
  page,
  focusedSeconds,
  onStarted,
  onEnded,
  onCancelled,
  onActive
}: Props): React.JSX.Element {
  const [chunks, setChunks] = useState<ChunkInfo[] | null>(null)
  const [active, setActive] = useState<StudySession | null>(null)
  const [saved, setSaved] = useState<StudySession | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [nodes, setNodes] = useState<SyllabusNode[]>([])
  const [pick, setPick] = useState('')

  useEffect(() => {
    let alive = true
    getActiveSession()
      .then((s) => {
        if (!alive) return
        setActive(s)
        if (s && s.document_id === documentId) onActive?.(true)
      })
      .catch((e) => alive && setError(messageOf(e)))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load the running session once per document
  }, [documentId])

  useEffect(() => {
    let alive = true
    listChunks(documentId, page)
      .then((c) => alive && setChunks(c))
      .catch((e) => alive && setError(messageOf(e)))
    return () => {
      alive = false
    }
  }, [documentId, page])

  useEffect(() => {
    if (!saved?.needs_tagging) return
    let alive = true
    getSyllabusTree()
      .then((t) => alive && setNodes(leaves(t)))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [saved?.needs_tagging, saved?.id])

  const run = async (fn: () => Promise<void>): Promise<void> => {
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(messageOf(e))
    }
  }

  const here = active && active.document_id === documentId ? active : null
  const startPos = here?.start ? [here.start.page, here.start.ordinal] : null
  const beforeStart = (c: ChunkInfo): boolean =>
    !!startPos && (c.page < startPos[0] || (c.page === startPos[0] && c.ordinal < startPos[1]))

  return (
    <aside aria-label="Bookmarks" className="flex w-80 shrink-0 flex-col gap-3 overflow-auto">
      {error && (
        <div role="alert" className="rounded-lg border border-danger p-2 text-sm text-danger">
          {error}
        </div>
      )}

      {active && (
        <div role="status" className="rounded-lg border border-line p-3 text-sm">
          <p>
            Reading since page {active.start?.page}, paragraph {(active.start?.ordinal ?? 0) + 1} in{' '}
            <strong>{active.document_title}</strong>.
          </p>
          <Button
            className="mt-2"
            onClick={() =>
              run(async () => {
                await cancelSession(active.id)
                setActive(null)
                onCancelled?.()
              })
            }
          >
            Cancel session
          </Button>
        </div>
      )}

      {saved && (
        <section aria-label="Session saved" className="rounded-lg border border-line p-3 text-sm">
          <h2 className="font-semibold">Session saved</h2>
          <p className="text-muted">
            Pages {saved.start?.page}–{saved.end?.page}, {Math.round(saved.focused_seconds / 60)}{' '}
            min focused. The recall gate is next.
          </p>
          {saved.tags.length > 0 && (
            <ul className="mt-2 flex flex-wrap gap-1">
              {saved.tags.map((t) => (
                <li key={t.id} className="rounded border border-line px-1.5 text-xs">
                  {t.title}
                </li>
              ))}
            </ul>
          )}
          {saved.needs_tagging && (
            <div className="mt-2 flex flex-col gap-2">
              <p>No syllabus node matched automatically. Pick one:</p>
              <select
                aria-label="Syllabus node"
                value={pick}
                onChange={(e) => setPick(e.target.value)}
                className="min-h-10 rounded-lg border border-line bg-app-bg px-2"
              >
                <option value="">Choose a node…</option>
                {nodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.title}
                  </option>
                ))}
              </select>
              <Button
                disabled={!pick}
                onClick={() => run(async () => setSaved(await setSessionTags(saved.id, [pick])))}
              >
                Save tag
              </Button>
            </div>
          )}
          {saved.source_budget.map((b) => (
            <p key={b.node_id} className="mt-2 rounded border border-warning p-2 text-warning">
              “{b.title}” now has {b.sources} sources. Top rankers use fewer sources and revise
              more.
            </p>
          ))}
        </section>
      )}

      <h2 className="text-sm font-semibold">Page {page} paragraphs</h2>
      {chunks && chunks.length === 0 && (
        <p className="text-sm text-muted">No readable text on this page (it may be an image).</p>
      )}
      <ol className="flex flex-col gap-2">
        {chunks?.map((c) => (
          <li key={c.id} className="rounded-lg border border-line p-2 text-sm">
            <p className="mb-2 text-muted">{snippet(c.text)}</p>
            {here ? (
              <Button
                disabled={beforeStart(c)}
                aria-label={`Set end bookmark at paragraph ${c.ordinal + 1}`}
                onClick={() =>
                  run(async () => {
                    const s = await endSession(here.id, c.id, focusedSeconds)
                    setActive(null)
                    onEnded?.()
                    setSaved(s)
                    setPick('')
                  })
                }
              >
                End here
              </Button>
            ) : (
              <Button
                aria-label={`Set start bookmark at paragraph ${c.ordinal + 1}`}
                disabled={!!active}
                onClick={() =>
                  run(async () => {
                    setActive(await startSession(documentId, c.id))
                    setSaved(null)
                    onStarted?.()
                  })
                }
              >
                Start here
              </Button>
            )}
          </li>
        ))}
      </ol>
    </aside>
  )
}
