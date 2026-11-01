import type { ScreenId } from '@jarvis/shared'
import { Button } from '../components/ui/button'
import { EmptyState } from '../components/empty-state'
import { SCREEN_META } from '../screens'

/** Placeholder screen: heading, one-line purpose and an empty state with ONE primary action. */
export function ScreenView({ id }: { id: ScreenId }): React.JSX.Element {
  const m = SCREEN_META[id]
  return (
    <section className="flex max-w-3xl flex-col gap-6">
      <header>
        <h1 className="text-3xl font-semibold tracking-tight">{m.label}</h1>
        <p className="mt-1 text-muted">{m.description}</p>
      </header>
      <EmptyState
        title={m.emptyTitle}
        body={m.emptyBody}
        action={<Button variant="primary">{m.primaryAction}</Button>}
      />
    </section>
  )
}
