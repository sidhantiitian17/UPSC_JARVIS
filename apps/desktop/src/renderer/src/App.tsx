import { HashRouter } from 'react-router-dom'
import { AppRoutes } from './routes'
import { GateProvider } from './gate/gate-host'
import { TimerProvider } from './timer/timer-context'

function App(): React.JSX.Element {
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
