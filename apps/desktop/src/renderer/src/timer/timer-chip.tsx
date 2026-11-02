import { Button } from '../components/ui/button'
import { useTimer } from './timer-context'

/** Sidebar countdown. Hidden while no block is running. */
export function TimerChip(): React.JSX.Element | null {
  const t = useTimer()
  const s = t.state
  if (s.status === 'idle') return null

  const label = s.kind === 'break' ? 'Break' : 'Focus'
  return (
    <div
      role="timer"
      aria-label={`${label} timer`}
      className="rounded-lg border border-line p-3 text-sm max-[1200px]:hidden"
    >
      {s.status === 'expired' ? (
        <p className="font-semibold">{s.kind === 'break' ? 'Break is over' : 'Time is up'}</p>
      ) : (
        <>
          <p className="text-xs text-muted">{label}</p>
          <p className="font-mono text-2xl tabular-nums">{t.clock}</p>
          {s.status === 'paused' && (
            <p className="text-xs text-muted">
              {s.reason === 'idle' ? 'Paused: you were away' : 'Paused'}
            </p>
          )}
          <Button
            className="mt-2"
            aria-label={s.status === 'paused' ? 'Resume timer' : 'Pause timer'}
            onClick={s.status === 'paused' ? t.resume : t.pause}
          >
            {s.status === 'paused' ? 'Resume' : 'Pause'}
          </Button>
        </>
      )}
    </div>
  )
}
