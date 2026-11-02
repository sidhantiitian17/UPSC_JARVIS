import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getReviewStats, type ReviewStats } from '../api/client'
import { EmptyState } from '../components/empty-state'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'
import { ReviewSession } from '../review/review-session'
import { SCREEN_META } from '../screens'

export function TodayScreen(): React.JSX.Element {
  const m = SCREEN_META.today
  const navigate = useNavigate()
  const [stats, setStats] = useState<ReviewStats | null>(null)
  const [reviewing, setReviewing] = useState(false)
  const [reloads, setReloads] = useState(0)

  useEffect(() => {
    let alive = true
    getReviewStats()
      .then((s) => alive && setStats(s))
      .catch(() => undefined) // the dashboard still works without stats
    return () => {
      alive = false
    }
  }, [reloads])

  const dueToday = stats ? Math.min(stats.due_now, stats.remaining_today) : 0
  const hasDue = dueToday > 0

  if (reviewing)
    return (
      <ReviewSession
        onClose={() => {
          setReviewing(false)
          setReloads((n) => n + 1)
        }}
      />
    )

  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{m.label}</h1>
        <p className="mt-1 text-muted">{m.description}</p>
      </header>

      {hasDue ? (
        <Card className="flex flex-col items-start gap-3">
          <h2 className="text-xl font-semibold">Review</h2>
          <p>
            {stats!.due_now} cards due · {stats!.remaining_today} left today
          </p>
          <Button variant="primary" onClick={() => setReviewing(true)}>
            Start review
          </Button>
        </Card>
      ) : (
        <EmptyState
          title={m.emptyTitle}
          body={m.emptyBody}
          action={
            <Button variant="primary" onClick={() => navigate('/study')}>
              Start studying
            </Button>
          }
        />
      )}
    </section>
  )
}
