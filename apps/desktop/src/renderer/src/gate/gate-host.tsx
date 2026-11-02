/* eslint-disable react-refresh/only-export-components -- the provider and its hook belong together */
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAwaitingGate } from '../api/client'
import { GateView, type GateClose } from './gate-view'

type OpenArgs = { sessionId: number; documentId: number }
type ReaderRequest = { documentId: number; page: number }

type GateApi = {
  openGate: (a: OpenArgs) => void
  /** open a book on a page in the Study screen (used by Today's "Continue reading") */
  requestReader: (r: ReaderRequest) => void
  /** set when the owner chose "review page N" after a failed gate; the Study screen consumes it */
  readerRequest: ReaderRequest | null
  clearReaderRequest: () => void
}

const GateContext = createContext<GateApi>({
  openGate: () => undefined,
  requestReader: () => undefined,
  readerRequest: null,
  clearReaderRequest: () => undefined
})
export const useGate = (): GateApi => useContext(GateContext)

export function GateProvider({ children }: { children: React.ReactNode }): React.JSX.Element {
  const navigate = useNavigate()
  const [open, setOpen] = useState<OpenArgs | null>(null)
  const [readerRequest, setReaderRequest] = useState<ReaderRequest | null>(null)

  // A gate that was never finished (app closed mid-quiz) reopens on the next launch.
  useEffect(() => {
    let alive = true
    getAwaitingGate()
      .then((s) => alive && s && setOpen({ sessionId: s.id, documentId: s.document_id }))
      .catch(() => undefined)
    return () => {
      alive = false
    }
  }, [])

  const close = useCallback(
    (r?: GateClose) => {
      const args = open
      setOpen(null)
      if (r?.openPage && args) {
        setReaderRequest(r.openPage)
        navigate('/study')
      }
    },
    [open, navigate]
  )

  const api = useMemo<GateApi>(
    () => ({
      openGate: setOpen,
      requestReader: (r) => {
        setReaderRequest(r)
        navigate('/study')
      },
      readerRequest,
      clearReaderRequest: () => setReaderRequest(null)
    }),
    [readerRequest, navigate]
  )

  return (
    <GateContext.Provider value={api}>
      {children}
      {open && (
        <GateView
          key={open.sessionId}
          sessionId={open.sessionId}
          documentId={open.documentId}
          onClose={close}
        />
      )}
    </GateContext.Provider>
  )
}
