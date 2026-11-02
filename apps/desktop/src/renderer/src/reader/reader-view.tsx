import { useCallback, useEffect, useRef, useState } from 'react'
import { getDocumentFile, getDocumentInfo, savePosition, type LibraryDocument } from '../api/client'
import { Button } from '../components/ui/button'
import type { PdfDocHandle, PdfEngine } from './pdf-engine'
import { BookmarkPanel } from './bookmark-panel'
import { pdfjsEngine } from './pdfjs-engine'
import { ZOOM_STEPS, clampPage, nextZoom } from './reader-state'

function decodeBase64(b64: string): Uint8Array {
  const bin = atob(b64)
  const out = new Uint8Array(bin.length)
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i)
  return out
}

function describe(e: unknown): string {
  const detail = (e as { body?: { detail?: string } } | null)?.body?.detail
  if (detail) return detail
  return `Could not open this PDF${e instanceof Error && e.message ? ` (${e.message})` : ''}.`
}

type Props = { documentId: number; onBack: () => void; engine?: PdfEngine }

export function ReaderView({ documentId, onBack, engine = pdfjsEngine }: Props): React.JSX.Element {
  const [doc, setDoc] = useState<LibraryDocument | null>(null)
  const [pdf, setPdf] = useState<PdfDocHandle | null>(null)
  const [page, setPage] = useState(1)
  const [zoom, setZoom] = useState<'fit' | number>('fit')
  const [invert, setInvert] = useState(() => document.documentElement.dataset.theme !== 'light')
  const [error, setError] = useState<string | null>(null)
  const [pageText, setPageText] = useState('1')
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const textRef = useRef<HTMLDivElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(1)
  const savedPage = useRef(1)
  const total = pdf?.numPages ?? doc?.page_count ?? 1

  useEffect(() => {
    let alive = true
    let handle: PdfDocHandle | null = null
    ;(async () => {
      try {
        const info = await getDocumentInfo(documentId)
        const file = await getDocumentFile(documentId)
        const opened = await engine.open(decodeBase64(file.base64))
        if (!alive) return opened.destroy()
        handle = opened
        const start = clampPage(info.last_page, opened.numPages)
        savedPage.current = start
        setDoc(info)
        setPage(start)
        setPageText(String(start))
        setPdf(opened)
      } catch (e) {
        if (alive) setError(describe(e))
      }
    })()
    return () => {
      alive = false
      handle?.destroy()
    }
  }, [documentId, engine])

  useEffect(() => {
    if (!pdf || !canvasRef.current || !textRef.current) return
    let alive = true
    pdf
      .getPage(page)
      .then(async (p) => {
        const width = scrollRef.current?.clientWidth ?? 0
        const next = zoom === 'fit' ? (width > 48 ? (width - 32) / p.baseWidth : 1) : zoom
        if (!alive) return
        setScale(next)
        if (canvasRef.current && textRef.current)
          await p.render(canvasRef.current, textRef.current, next)
      })
      .catch((e) => alive && setError(describe(e)))
    return () => {
      alive = false
    }
  }, [pdf, page, zoom])

  useEffect(() => {
    if (!pdf || page === savedPage.current) return
    const t = setTimeout(() => {
      savePosition(documentId, page)
        .then(() => (savedPage.current = page))
        .catch(() => undefined) // position is best-effort; reading must never be interrupted
    }, 300)
    return () => clearTimeout(t)
  }, [pdf, page, documentId])

  const goTo = useCallback(
    (p: number) => {
      const next = clampPage(p, total)
      setPage(next)
      setPageText(String(next))
    },
    [total]
  )

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if ((e.target as HTMLElement | null)?.tagName === 'INPUT') return
      if (e.key === 'ArrowRight' || e.key === 'PageDown') goTo(page + 1)
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp') goTo(page - 1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [goTo, page])

  const stepZoom = (dir: 1 | -1): void => {
    const next = nextZoom(scale, dir)
    if (next !== undefined) setZoom(next)
  }
  const atMax = scale >= ZOOM_STEPS[ZOOM_STEPS.length - 1]
  const atMin = scale <= ZOOM_STEPS[0]

  return (
    <section className="flex h-full flex-col gap-3">
      <header className="flex flex-wrap items-center gap-2">
        <Button onClick={onBack}>Back to library</Button>
        <h1 className="mr-auto text-xl font-semibold">{doc?.title ?? 'Reader'}</h1>
        <Button aria-label="Previous page" disabled={page <= 1} onClick={() => goTo(page - 1)}>
          ‹
        </Button>
        <input
          type="number"
          aria-label="Page number"
          min={1}
          max={total}
          value={pageText}
          onChange={(e) => setPageText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && goTo(Number(pageText))}
          onBlur={() => goTo(Number(pageText))}
          className="min-h-10 w-20 rounded-lg border border-line bg-app-bg px-2 text-center text-sm"
        />
        <span className="text-sm text-muted">of {total}</span>
        <Button aria-label="Next page" disabled={page >= total} onClick={() => goTo(page + 1)}>
          ›
        </Button>
        <Button aria-label="Zoom out" disabled={atMin} onClick={() => stepZoom(-1)}>
          −
        </Button>
        <Button aria-label="Zoom in" disabled={atMax} onClick={() => stepZoom(1)}>
          +
        </Button>
        <Button aria-label="Fit width" onClick={() => setZoom('fit')}>
          Fit
        </Button>
        <Button aria-label="Dark pages" aria-pressed={invert} onClick={() => setInvert(!invert)}>
          Dark pages
        </Button>
      </header>

      {error && (
        <div role="alert" className="rounded-lg border border-danger p-3 text-sm text-danger">
          {error}
        </div>
      )}

      <div className="flex min-h-0 flex-1 gap-3">
        <div
          ref={scrollRef}
          className="min-h-0 flex-1 overflow-auto rounded-card border border-line bg-surface-2 p-4"
        >
          <div
            data-testid="page-stage"
            data-invert={String(invert)}
            className="relative mx-auto w-fit"
          >
            <canvas
              ref={canvasRef}
              style={invert ? { filter: 'invert(1) hue-rotate(180deg)' } : undefined}
              aria-label={`Page ${page}`}
            />
            <div ref={textRef} className="textLayer absolute left-0 top-0" />
          </div>
        </div>
        <BookmarkPanel documentId={documentId} page={page} />
      </div>
    </section>
  )
}
