import { Navigate, Route, Routes } from 'react-router-dom'
import { SCREENS } from '@jarvis/shared'
import { Shell } from './Shell'
import { NotFound } from './screens/not-found'
import { ScreenView } from './screens/screen-view'
import { SettingsScreen } from './screens/settings-screen'
import { SyllabusScreen } from './screens/syllabus-screen'

const SCREEN_ELEMENT: Partial<Record<(typeof SCREENS)[number], React.JSX.Element>> = {
  settings: <SettingsScreen />,
  syllabus: <SyllabusScreen />
}

export function AppRoutes(): React.JSX.Element {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Navigate to="/today" replace />} />
        {SCREENS.map((id) => (
          <Route key={id} path={id} element={SCREEN_ELEMENT[id] ?? <ScreenView id={id} />} />
        ))}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}
