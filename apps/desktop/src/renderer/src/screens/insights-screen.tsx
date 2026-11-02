import { useEffect, useState } from 'react'
import {
  getFocusSummary,
  getPyqDrift,
  getPyqTrends,
  getTruth,
  type FocusSummary,
  type PyqDrift,
  type PyqTrends,
  type Truth
} from '../api/client'
import { Card } from '../components/ui/card'
import { SCREEN_META } from '../screens'

function DayRow({
  d,
  max
}: {
  d: Truth['weekly']['days'][number]
  max: number
}): React.JSX.Element {
  const w = (h: number): string => `${max > 0 ? Math.round((100 * h) / max) : 0}%`
  return (
    <li data-testid="day-row" className="grid grid-cols-[5rem_1fr_9rem] items-center gap-3 text-sm">
      <span className="text-muted">{d.date.slice(5)}</span>
      <span className="flex flex-col gap-1" aria-hidden>
        <span className="h-2 rounded-full bg-line" style={{ width: w(d.claimed_hours) }} />
        <span className="h-2 rounded-full bg-accent" style={{ width: w(d.verified_hours) }} />
      </span>
      <span>
        {d.claimed_hours} claimed · {d.verified_hours} verified
      </span>
    </li>
  )
}

export function InsightsScreen(): React.JSX.Element {
  const m = SCREEN_META.insights
  const [data, setData] = useState<Truth | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [focus, setFocus] = useState<FocusSummary | null>(null)
  const [pyq, setPyq] = useState<{ trends: PyqTrends; drift: PyqDrift } | null>(null)

  useEffect(() => {
    let alive = true
    getTruth()
      .then((t) => alive && setData(t))
      .catch(() => alive && setError('Could not load your insights. Is the local service running?'))
    getFocusSummary()
      .then((f) => alive && setFocus(f))
      .catch(() => undefined)
    Promise.all([getPyqTrends(), getPyqDrift()])
      .then(([trends, drift]) => alive && setPyq({ trends, drift }))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])

  const max = data
    ? Math.max(1, ...data.weekly.days.map((d) => Math.max(d.claimed_hours, d.verified_hours)))
    : 1

  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{m.label}</h1>
        <p className="mt-1 text-muted">{m.description}</p>
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-danger p-3 text-sm text-danger">
          {error}
        </div>
      )}

      {data && (
        <>
          <Card>
            <section aria-label="Claimed versus verified" className="flex flex-col gap-3">
              <h2 className="text-xl font-semibold">Claimed versus verified, last 7 days</h2>
              <p>
                {data.weekly.claimed_hours} h claimed · {data.weekly.verified_hours} h verified
                {data.weekly.verified_share !== null && (
                  <span> · {data.weekly.verified_share}% verified</span>
                )}
              </p>
              <ul className="flex flex-col gap-2">
                {data.weekly.days.map((d) => (
                  <DayRow key={d.date} d={d} max={max} />
                ))}
              </ul>
              <p className="text-xs text-muted">
                Claimed is all focused time. Verified is only time whose recall gate passed.
              </p>
            </section>
          </Card>

          <Card className="flex flex-col gap-3">
            <h2 className="text-xl font-semibold">Calibration</h2>
            <table aria-label="Calibration" className="w-full text-sm">
              <thead>
                <tr className="text-left text-muted">
                  <th>Tag</th>
                  <th>Accuracy</th>
                  <th>Expected</th>
                  <th>Answers</th>
                </tr>
              </thead>
              <tbody>
                {data.calibration.map((c) => (
                  <tr key={c.tag}>
                    <td className="font-semibold">{c.tag}</td>
                    <td>
                      {c.enough_data && c.accuracy !== null ? `${c.accuracy}%` : 'Not enough data'}
                    </td>
                    <td>{c.expected}</td>
                    <td>{c.answers}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="text-xs text-muted">
              G = sure, A = 50-50, R = guess. Accuracy close to the expected band means your
              confidence is trustworthy.
            </p>
          </Card>

          <Card className="flex flex-col gap-1">
            <h2 className="text-xl font-semibold">Pace forecast</h2>
            <p>
              {data.forecast.days_left} days left until {data.forecast.exam_date}
              {data.forecast.assumed_exam_date && (
                <span className="text-muted"> (assumed exam date)</span>
              )}
            </p>
            <p>
              {data.forecast.avg_daily_verified_minutes} verified min per day over the last 28 days
            </p>
            <p>
              About {data.forecast.projected_verified_hours} verified hours by then at this pace.
            </p>
          </Card>

          <Card>
            <section aria-label="During focus blocks" className="flex flex-col gap-1">
              <h2 className="text-xl font-semibold">During focus blocks, last 7 days</h2>
              {focus?.enabled ? (
                <>
                  <p>
                    {focus.totals.study_minutes} min study · {focus.totals.neutral_minutes} min
                    neutral · {focus.totals.distraction_minutes} min distraction
                  </p>
                  {focus.top_distraction_apps.length > 0 && (
                    <p className="text-sm text-muted">
                      Most distracting apps:{' '}
                      {focus.top_distraction_apps
                        .map((a) => `${a.app} (${a.minutes} min)`)
                        .join(', ')}
                    </p>
                  )}
                </>
              ) : (
                <p className="text-sm text-muted">
                  Focus Guard is off. Turn it on in Settings if you want to see where focus blocks
                  go.
                </p>
              )}
            </section>
          </Card>

          {pyq && (
            <Card>
              <section aria-label="PYQ weightage versus your time" className="flex flex-col gap-3">
                <h2 className="text-xl font-semibold">PYQ weightage versus your time</h2>
                <p className="text-sm text-muted">
                  {pyq.trends.tagged_pct === null
                    ? 'No PYQ text is imported yet. Import and tag PYQs in the PYQ Lab.'
                    : `${pyq.trends.tagged_pct}% of questions with text are tagged (${pyq.trends.tagged_questions} of ${pyq.trends.questions_with_text}). Only tags you accepted are counted.`}
                </p>
                {!pyq.drift.enough_data && <p className="text-sm">{pyq.drift.message}</p>}
                {pyq.drift.alerts.map((a) => (
                  <p
                    key={a.subject_id}
                    role="alert"
                    className="rounded-lg border border-warning p-2 text-sm"
                  >
                    {a.text}
                  </p>
                ))}
                {pyq.drift.rows.length > 0 && (
                  <table aria-label="Weightage and time" className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-muted">
                        <th>Subject</th>
                        <th>PYQ weightage</th>
                        <th>Your verified time (4 weeks)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {pyq.drift.rows.map((r) => (
                        <tr key={r.subject_id}>
                          <td>{r.title}</td>
                          <td>{r.weight_share_pct}%</td>
                          <td>{r.time_share_pct}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </section>
            </Card>
          )}

          <Card className="flex flex-col gap-2">
            <h2 className="text-xl font-semibold">Weekly honesty report</h2>
            <ul className="flex list-disc flex-col gap-1 pl-5">
              {data.report.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </Card>
        </>
      )}
    </section>
  )
}
