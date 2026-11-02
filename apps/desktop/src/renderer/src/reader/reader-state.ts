export const ZOOM_STEPS = [0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3] as const

export const clampPage = (p: number, total: number): number =>
  Math.min(Math.max(Math.round(p) || 1, 1), Math.max(total, 1))

/** Next zoom step above (dir 1) or below (dir -1) the current scale, or undefined at the limit. */
export function nextZoom(current: number, dir: 1 | -1): number | undefined {
  return dir === 1
    ? ZOOM_STEPS.find((s) => s > current + 1e-6)
    : [...ZOOM_STEPS].reverse().find((s) => s < current - 1e-6)
}
