import { useEffect, useState } from 'react'
import { ApiError, getSyllabusTree, reloadSyllabus, type SyllabusNode } from '../api/client'
import { EmptyState } from '../components/empty-state'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'
import { SCREEN_META } from '../screens'

const KIND_LABEL: Record<string, string> = {
  paper: 'Paper',
  subject: 'Subject',
  topic: 'Topic',
  microtheme: 'Micro-theme',
  thinker: 'Thinker',
  concept: 'Concept'
}

function reloadError(e: unknown): string {
  if (e instanceof ApiError && e.status === 422) {
    const detail = (e.body as { detail?: string } | null)?.detail
    return `The syllabus files have a problem: ${detail ?? 'invalid ontology'}`
  }
  return 'Could not reload the syllabus files.'
}

function TreeNode({ node, depth }: { node: SyllabusNode; depth: number }): React.JSX.Element {
  const [open, setOpen] = useState(depth === 0)
  const hasChildren = node.children.length > 0
  return (
    <li role="treeitem" aria-expanded={hasChildren ? open : undefined} aria-selected={false}>
      <div className="flex items-center gap-2 py-1" style={{ paddingLeft: depth * 20 }}>
        {hasChildren ? (
          <button
            type="button"
            aria-expanded={open}
            aria-label={`${open ? 'Collapse' : 'Expand'} ${node.title}`}
            onClick={() => setOpen(!open)}
            className="inline-flex h-8 w-8 items-center justify-center rounded text-muted hover:bg-surface-2"
          >
            <span aria-hidden>{open ? '▾' : '▸'}</span>
          </button>
        ) : (
          <span className="inline-block h-8 w-8" aria-hidden />
        )}
        <span className="font-medium">{node.title}</span>
        <span className="text-xs text-muted">{KIND_LABEL[node.kind] ?? node.kind}</span>
        <span
          className="rounded border border-line px-1.5 text-xs text-muted"
          title={
            node.reviewed
              ? 'Reviewed by the owner'
              : 'Draft: not yet reviewed against the official syllabus'
          }
        >
          {node.reviewed ? 'Reviewed' : 'Draft'}
        </span>
      </div>
      {hasChildren && open && (
        <ul role="group">
          {node.children.map((c) => (
            <TreeNode key={c.id} node={c} depth={depth + 1} />
          ))}
        </ul>
      )}
    </li>
  )
}

export function SyllabusScreen(): React.JSX.Element {
  const m = SCREEN_META.syllabus
  const [tree, setTree] = useState<SyllabusNode[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reloading, setReloading] = useState(false)

  useEffect(() => {
    let alive = true
    getSyllabusTree()
      .then((t) => alive && setTree(t))
      .catch(() => alive && setError('Could not load the syllabus. Is the local service running?'))
    return () => {
      alive = false
    }
  }, [])

  const reload = async (): Promise<void> => {
    setReloading(true)
    setError(null)
    try {
      await reloadSyllabus()
      setTree(await getSyllabusTree())
    } catch (e) {
      setError(reloadError(e))
    } finally {
      setReloading(false)
    }
  }

  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">{m.label}</h1>
          <p className="mt-1 text-muted">{m.description}</p>
        </div>
        {tree && tree.length > 0 && (
          <Button onClick={reload} disabled={reloading} aria-label="Reload syllabus files">
            Reload
          </Button>
        )}
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-danger p-3 text-sm text-danger">
          {error}
        </div>
      )}

      {tree && tree.length === 0 && (
        <EmptyState
          title={m.emptyTitle}
          body={m.emptyBody}
          action={
            <Button
              variant="primary"
              onClick={reload}
              disabled={reloading}
              aria-label="Reload syllabus files"
            >
              {m.primaryAction}
            </Button>
          }
        />
      )}

      {tree && tree.length > 0 && (
        <Card>
          <ul role="tree" aria-label="Syllabus">
            {tree.map((n) => (
              <TreeNode key={n.id} node={n} depth={0} />
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted">
            Draft means the node is not yet verified against the official syllabus. Progress is
            never counted on unreviewed structure alone.
          </p>
        </Card>
      )}
    </section>
  )
}
