import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { SCREENS } from '@jarvis/shared'
import { AppRoutes } from './routes'

function renderAt(path = '/'): ReturnType<typeof render> {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>
  )
}

describe('app shell', () => {
  it('lists every screen in the sidebar in the shared order', () => {
    renderAt()
    const nav = screen.getByRole('navigation', { name: /main/i })
    const hrefs = within(nav)
      .getAllByRole('link')
      .map((a) => a.getAttribute('href'))
    expect(hrefs).toEqual(SCREENS.map((s) => `/${s}`))
  })

  it('opens Today by default', () => {
    renderAt('/')
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/today/i)
  })

  it.each(
    SCREENS.filter(
      (s) =>
        s !== 'settings' && s !== 'syllabus' && s !== 'study' && s !== 'today' && s !== 'insights'
    )
  )('screen "%s" has a heading, an empty state and exactly one primary action', (id) => {
    renderAt(`/${id}`)
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(screen.getByTestId('empty-state')).toBeInTheDocument()
    const primary = screen
      .getAllByRole('button')
      .filter((b) => b.getAttribute('data-variant') === 'primary')
    expect(primary).toHaveLength(1)
  })

  it('navigates when a sidebar link is clicked and marks it current', async () => {
    renderAt('/today')
    const nav = screen.getByRole('navigation', { name: /main/i })
    await userEvent.click(within(nav).getByRole('link', { name: /syllabus/i }))
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/syllabus/i)
    expect(within(nav).getByRole('link', { name: /syllabus/i })).toHaveAttribute(
      'aria-current',
      'page'
    )
  })

  it('shows a friendly not-found screen for unknown routes', () => {
    renderAt('/nope')
    expect(screen.getByText(/not found/i)).toBeInTheDocument()
  })
})
