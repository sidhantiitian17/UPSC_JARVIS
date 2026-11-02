import { useEffect, useState } from 'react'
import {
  commitPlan,
  getPlannerStatus,
  makePlan,
  type DayPlan,
  type PlannerStatus
} from '../api/client'
import { Button } from '../components/ui/button'
import { Card } from '../components/ui/card'

const LABEL: Record<string, string> = {
  review: 'Review',
  study: 'Study',
  break: 'Break',
  catch_up: 'Catch-up gate'
}

export function PlanCard(): React.JSX.Element {
  const [hours, setHours] = useState('4')
  const [plan, setPlan] = useState<DayPlan | null>(null)
  const [status, setStatus] = useState<PlannerStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [committed, setCommitted] = useState(false)

  useEffect(() => {
    let alive = true
    getPlannerStatus()
      .then((s) => alive && setStatus(s))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])

  const valid = (): number | null => {
    const n = Number(hours)
    if (!Number.isFinite(n) || n < 1 || n > 16) {
      setError('Free hours must be between 1 and 16.')
      return null
    }
    setError(null)
    return n
  }

  const make = async (): Promise<void> => {
    const n = valid()
    if (n === null) return
    try {
      setPlan(await makePlan(n))
      setCommitted(false)
    } catch {
      setError('Could not build a plan. Is the local service running?')
    }
  }

  const commit = async (): Promise<void> => {
    const n = valid()
    if (n === null) return
    try {
      await commitPlan(n)
      setCommitted(true)
    } catch {
      setError('Could not save the plan.')
    }
  }

  return (
    <Card className="flex flex-col gap-3">
      <h2 className="text-xl font-semibold">Plan my day</h2>

      {status?.yesterday && (
        <p className="text-sm text-muted">
          Yesterday: {status.yesterday.verified_minutes} of {status.yesterday.committed_minutes} min
          verified.
        </p>
      )}
      {status?.committed_today && (
        <p className="text-sm">
          You committed to {status.committed_today.study_minutes} min of study today.
        </p>
      )}

      <div className="flex items-end gap-3">
        <label className="flex flex-col gap-1 text-sm">
          Free hours today
          <input
            type="number"
            min={1}
            max={16}
            step={0.5}
            aria-label="Free hours"
            value={hours}
            onChange={(e) => setHours(e.target.value)}
            className="min-h-10 w-24 rounded-lg border border-line bg-app-bg px-3"
          />
        </label>
        <Button onClick={make}>Make plan</Button>
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-danger p-2 text-sm text-danger">
          {error}
        </div>
      )}

      {plan && (
        <>
          {plan.notes.map((n) => (
            <p key={n} className="rounded-lg border border-line p-2 text-sm">
              {n}
            </p>
          ))}
          <ol aria-label="Today's plan" className="flex flex-col gap-1">
            {plan.blocks.map((b, i) => (
              <li
                key={i}
                className="flex items-baseline justify-between gap-4 border-b border-line py-1 text-sm last:border-0"
              >
                <span>
                  <span className="font-semibold">{LABEL[b.kind] ?? b.kind}</span>
                  {b.subject && <span>: {b.subject}</span>}
                  <span className="ml-2 text-muted">{b.reason}</span>
                </span>
                <span>{b.minutes} min</span>
              </li>
            ))}
          </ol>
          <p className="text-xs text-muted">
            {plan.planned_minutes} of {plan.free_minutes} min planned
          </p>
          {committed ? (
            <p role="status">
              Plan committed. Tomorrow you will see how it went, with no pressure.
            </p>
          ) : (
            <Button onClick={commit}>Commit to this plan</Button>
          )}
        </>
      )}
    </Card>
  )
}
