import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getGuard,
  getProgress,
  getToday,
  setBadDay,
  type GameProgress,
  type GuardStatus,
  type TodayDashboard
} from '../api/client'
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

function ProgressCard({ g }: { g: GameProgress }): React.JSX.Element {
  const span = g.xp_into_level + g.xp_to_next_level
  const pct = span > 0 ? Math.round((100 * g.xp_into_level) / span) : 0
  const remaining = Math.max(0, g.today_goal - g.today_minutes)
  return (
    <Card className="flex flex-col gap-2">
      <h2 className="text-xl font-semibold">Level {g.level}</h2>
      <p>{g.xp_total} XP</p>
      <div
        role="progressbar"
        aria-label={`XP to level ${g.level + 1}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        className="h-2 overflow-hidden rounded-full bg-surface-2"
      >
        <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
      <p className="text-sm text-muted">
        {g.xp_to_next_level} XP to level {g.level + 1}
      </p>
      <p>
        {g.streak}-day streak
        {g.freezes > 0 && (
          <span className="text-muted">
            {' '}
            · {g.freezes} streak {g.freezes === 1 ? 'freeze' : 'freezes'}
          </span>
        )}
      </p>
      <p className="text-sm">
        {g.today_minutes} of {g.today_goal} min today
        {g.at_risk && remaining > 0 && <span> · {remaining} more min keeps your streak going</span>}
      </p>
      {g.comeback.active && (
        <p className="rounded-lg border border-line p-2 text-sm">
          Comeback quest: {g.comeback.days_done} of {g.comeback.days_needed} goal days. Reach your
          daily goal {g.comeback.days_needed - g.comeback.days_done} more time(s) in a row to win
          your streak back.
        </p>
      )}
      <p className="text-xs text-muted">XP comes only from minutes that passed the recall gate.</p>
    </Card>
  )
}

function GuardCard({
  g,
  onToggle
}: {
  g: GuardStatus
  onToggle: (active: boolean) => void
}): React.JSX.Element {
  return (
    <Card className="flex flex-col items-start gap-2">
      {g.messages.map((m) => (
        <p key={m} role="status">
          {m}
        </p>
      ))}
      {g.bad_day.today_active ? (
        <>
          <p>Bad-day mode is on for today. {g.bad_day.note}</p>
          <Button onClick={() => onToggle(false)}>Back to the normal goal</Button>
        </>
      ) : (
        <Button onClick={() => onToggle(true)} aria-label="Having a rough day? Use bad-day mode">
          Having a rough day?
        </Button>
      )}
    </Card>
  )
}

export function TodayScreen(): React.JSX.Element {
  const m = SCREEN_META.today
  const navigate = useNavigate()
  const gate = useGate()
  const [data, setData] = useState<TodayDashboard | null>(null)
  const [game, setGame] = useState<GameProgress | null>(null)
  const [guard, setGuard] = useState<GuardStatus | null>(null)
  const [reviewing, setReviewing] = useState(false)
  const [reloads, setReloads] = useState(0)

  useEffect(() => {
    let alive = true
    getToday()
      .then((d) => alive && setData(d))
      .catch(() => undefined) // the dashboard still renders its empty state without data
    getProgress()
      .then((g) => alive && setGame(g))
      .catch(() => undefined)
    getGuard()
      .then((g) => alive && setGuard(g))
      .catch(() => undefined)
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

      {guard && (
        <GuardCard
          g={guard}
          onToggle={async (active) => {
            try {
              setGuard(await setBadDay(active))
              setReloads((n) => n + 1)
            } catch {
              /* keep the card as it was; the next refresh shows the real state */
            }
          }}
        />
      )}

      {game && <ProgressCard g={game} />}

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
