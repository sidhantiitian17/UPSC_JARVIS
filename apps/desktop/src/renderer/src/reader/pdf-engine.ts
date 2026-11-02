/** Minimal PDF rendering contract, so the reader can be tested without a real renderer. */
export type PdfPageHandle = {
  /** Width of the page at scale 1 (CSS px), used for "fit width". */
  baseWidth: number
  /** Draws the page into `canvas` and builds a selectable text layer inside `textLayer`. */
  render: (canvas: HTMLCanvasElement, textLayer: HTMLElement, scale: number) => Promise<void>
}

export type PdfDocHandle = {
  numPages: number
  getPage: (n: number) => Promise<PdfPageHandle>
  destroy: () => void
}

export type PdfEngine = { open: (data: Uint8Array) => Promise<PdfDocHandle> }
