import { NavLink, Outlet } from 'react-router-dom'
import { APP_NAME, SCREENS } from '@jarvis/shared'
import { SCREEN_META } from './screens'
import { cn } from './lib/utils'

export function Shell(): React.JSX.Element {
  return (
    <div className="flex h-full">
      <aside className="flex w-60 shrink-0 flex-col gap-6 border-r border-line bg-surface p-4 max-[1200px]:w-16">
        <div className="px-2 text-lg font-semibold tracking-tight max-[1200px]:hidden">
          {APP_NAME}
        </div>
        <nav aria-label="Main" className="flex flex-col gap-1">
          {SCREENS.map((id) => {
            const { label, icon: Icon } = SCREEN_META[id]
            return (
              <NavLink
                key={id}
                to={`/${id}`}
                aria-label={label}
                className={({ isActive }) =>
                  cn(
                    'flex min-h-10 items-center gap-3 rounded-lg px-3 text-sm',
                    isActive ? 'bg-surface-2 font-semibold text-fg' : 'text-muted hover:text-fg'
                  )
                }
              >
                <Icon aria-hidden size={18} />
                <span className="max-[1200px]:hidden">{label}</span>
              </NavLink>
            )
          })}
        </nav>
      </aside>
      <main className="min-w-0 flex-1 overflow-auto p-8">
        <Outlet />
      </main>
    </div>
  )
}
