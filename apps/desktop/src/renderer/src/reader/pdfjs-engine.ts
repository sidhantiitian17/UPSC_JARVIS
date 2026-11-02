import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'
import type { PdfEngine } from './pdf-engine'

/** Real engine on pdf.js (Apache-2.0). pdf.js is imported lazily so unit tests never load it. */
export const pdfjsEngine: PdfEngine = {
  async open(data) {
    const pdfjs = await import('pdfjs-dist')
    pdfjs.GlobalWorkerOptions.workerSrc = workerUrl
    const task = pdfjs.getDocument({ data })
    const doc = await task.promise
    return {
      numPages: doc.numPages,
      destroy: () => void task.destroy(),
      getPage: async (n) => {
        const page = await doc.getPage(n)
        let current: { cancel: () => void } | null = null
        return {
          baseWidth: page.getViewport({ scale: 1 }).width,
          render: async (canvas, textLayer, scale) => {
            current?.cancel()
            const viewport = page.getViewport({ scale })
            const ratio = window.devicePixelRatio || 1
            canvas.width = Math.floor(viewport.width * ratio)
            canvas.height = Math.floor(viewport.height * ratio)
            canvas.style.width = `${Math.floor(viewport.width)}px`
            canvas.style.height = `${Math.floor(viewport.height)}px`
            textLayer.replaceChildren()
            textLayer.style.width = canvas.style.width
            textLayer.style.height = canvas.style.height
            textLayer.style.setProperty('--total-scale-factor', String(scale))
            const task = page.render({
              canvas,
              viewport,
              transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0]
            })
            current = task
            await task.promise
            const layer = new pdfjs.TextLayer({
              textContentSource: page.streamTextContent(),
              container: textLayer,
              viewport
            })
            await layer.render()
          }
        }
      }
    }
  }
}
