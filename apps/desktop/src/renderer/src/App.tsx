import { HashRouter } from 'react-router-dom'
import { AppRoutes } from './routes'
import { useEffect } from 'react'
import { getSettings } from './api/client'
import { GateProvider } from './gate/gate-host'
import { TimerProvider } from './timer/timer-context'

/** Tell the pet which mode the owner chose, once the service answers. */
function usePetModeSync(): void {
  useEffect(() => {
    let alive = true
    getSettings()
      .then((s) => {
        if (alive) void window.jarvis?.pet?.setMode(s.pet_mode)
      })
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])
}

function App(): React.JSX.Element {
  usePetModeSync()
  return (
    <TimerProvider>
      <HashRouter>
        <GateProvider>
          <AppRoutes />
        </GateProvider>
      </HashRouter>
    </TimerProvider>
  )
}

export default App
