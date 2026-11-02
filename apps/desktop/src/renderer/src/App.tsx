import { HashRouter } from 'react-router-dom'
import { AppRoutes } from './routes'
import { TimerProvider } from './timer/timer-context'

function App(): React.JSX.Element {
  return (
    <TimerProvider>
      <HashRouter>
        <AppRoutes />
      </HashRouter>
    </TimerProvider>
  )
}

export default App
