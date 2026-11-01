import type { ReactNode } from 'react'

type Props = { title: string; body: string; action: ReactNode }

export function EmptyState({ title, body, action }: Props): React.JSX.Element {
  return (
    <div
      data-testid="empty-state"
      className="flex flex-col items-start gap-3 rounded-card border border-dashed border-line p-8"
    >
      <h2 className="text-xl font-semibold">{title}</h2>
      <p className="max-w-prose text-muted">{body}</p>
      {action}
    </div>
  )
}
