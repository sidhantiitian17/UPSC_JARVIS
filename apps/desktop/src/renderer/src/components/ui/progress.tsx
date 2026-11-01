import { cn } from '../../lib/utils'

type Props = { value: number; label: string; className?: string }

/** Progress bar whose label always says what is being measured (DESIGN.md: "62% verified"). */
export function Progress({ value, label, className }: Props): React.JSX.Element {
  const pct = Math.max(0, Math.min(100, Math.round(value)))
  return (
    <div className={cn('w-full', className)}>
      <div className="mb-1 flex justify-between text-sm text-muted">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={pct}
        className="h-2 overflow-hidden rounded-full bg-surface-2"
      >
        <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
