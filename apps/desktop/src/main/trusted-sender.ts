/** IPC is only honoured for frames of our own UI: the dev server origin or the packaged file:// bundle. */
export function isTrustedSender(frameUrl: string, devUrl: string | undefined): boolean {
  let url: URL
  try {
    url = new URL(frameUrl)
  } catch {
    return false
  }
  if (url.protocol === 'file:') return true
  if (!devUrl) return false
  try {
    return url.origin === new URL(devUrl).origin
  } catch {
    return false
  }
}
