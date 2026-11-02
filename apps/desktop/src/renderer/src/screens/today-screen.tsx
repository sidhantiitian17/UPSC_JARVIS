import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getToday, type TodayDashboard } from '../api/client'
import { EmptyState } from '../components/empty-state'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'
import { useGate } from '../gate/gate-host'
import { ReviewSession } from '../review/review-session'
import { SCREEN_META } from '../screens'

function cellShade(minutes: number): string {
  if (minutes <= 0) return 'bg-surface-2'
  if (minutes < 30) return 'bg-accent/30'
  if (minutes < 60) return 'bg-accent/60'
  return 'bg-accent'
}

function Heatmap({ days }: { days: TodayDashboard['heatmap'] }): React.JSX.Element {
  return (
    <div
      role="img"
      aria-label="Verified minutes per day, last 12 weeks"
      className="grid grid-flow-col grid-rows-7 gap-1"
    >
      {days.map((d) => (
        <span
          key={d.date}
          data-cell
          title={`${d.date}: ${d.minutes} min verified`}
          className={`h-3 w-3 rounded-sm ${cellShade(d.minutes)}`}
        />
      ))}
    </div>
  )
}

export function TodayScreen(): React.JSX.Element {
  const m = SCREEN_META.today
  const navigate = useNavigate()
  const gate = useGate()
  const [data, setData] = useState<TodayDashboard | null>(null)
  const [reviewing, setReviewing] = useState(false)
  const [reloads, setReloads] = useState(0)

  useEffect(() => {
    let alive = true
    getToday()
      .then((d) => alive && setData(d))
      .catch(() => undefined) // the dashboard still renders its empty state without data
    return () => {
      alive = false
    }
  }, [reloads])

  if (reviewing)
    return (
      <ReviewSession
        onClose={() => {
          setReviewing(false)
          setReloads((n) => n + 1)
        }}
      />
    )

  const dueToday = data ? Math.min(data.due_cards, data.review_remaining_today) : 0
  const waiting = data?.awaiting_gate_session_id ?? null
  const next = data?.next_block ?? null
  // Exactly one primary action: finish the gate, else review, else read, else start.
  const primary = waiting ? 'gate' : dueToday > 0 ? 'review' : next ? 'read' : 'start'

  const variant = (id: string): 'primary' | undefined => (primary === id ? 'primary' : undefined)
  const hasAnything =
    !!data && (waiting !== null || dueToday > 0 || next !== null || data.verified_minutes_week > 0)

  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{m.label}</h1>
        <p className="mt-1 text-muted">{m.description}</p>
      </header>

      {waiting !== null && (
        <Card className="flex flex-col items-start gap-3">
          <p>Your recall gate is waiting. Progress only counts once you pass it.</p>
          <Button
            variant={variant('gate')}
            onClick={() =>
              gate.openGate({ sessionId: waiting, documentId: next?.document_id ?? 0 })
            }
          >
            Finish recall gate
          </Button>
        </Card>
      )}

      {data && (
        <Card className="flex flex-col gap-2">
          <h2 className="text-xl font-semibold">Verified retained minutes</h2>
          <p>{data.verified_minutes_today} min verified today</p>
          <p>{data.verified_minutes_week} min verified this week</p>
          <p className="text-xs text-muted">
            Only focused minutes whose session passed the recall gate are counted.
          </p>
          <Heatmap days={data.heatmap} />
        </Card>
      )}

      {dueToday > 0 && (
        <Card className="flex flex-col items-start gap-3">
          <h2 className="text-xl font-semibold">Review</h2>
          <p>
            {data!.due_cards} cards due · {data!.review_remaining_today} left today
          </p>
          <Button variant={variant('review')} onClick={() => setReviewing(true)}>
            Start review
          </Button>
        </Card>
      )}

      {next && (
        <Card className="flex flex-col items-start gap-3">
          <h2 className="text-xl font-semibold">Next block</h2>
          <p>
            {next.title}, page {next.page}
          </p>
          <Button
            variant={variant('read')}
            onClick={() => gate.requestReader({ documentId: next.document_id, page: next.page })}
          >
            Continue reading
          </Button>
        </Card>
      )}

      {!hasAnything && (
        <EmptyState
          title={m.emptyTitle}
          body={m.emptyBody}
          action={
            <Button variant={variant('start')} onClick={() => navigate('/study')}>
              Start studying
            </Button>
          }
        />
      )}
    </section>
  )
}
