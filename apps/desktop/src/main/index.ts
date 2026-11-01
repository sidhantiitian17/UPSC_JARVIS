import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import type { ApiRequest, SidecarState } from '@jarvis/shared'
import { createApiProxy } from './api-proxy'
import { resolveSidecarCommand, startSidecar, type RunningSidecar } from './sidecar'
import { realSidecarDeps } from './sidecar-runtime'
import { isTrustedSender } from './trusted-sender'
import { isAllowedExternalUrl, secureWebPreferences } from './window-options'

let sidecar: RunningSidecar | null = null
let proxy: ReturnType<typeof createApiProxy> | null = null
let sidecarState: SidecarState = { ready: false }

async function bootSidecar(): Promise<void> {
  try {
    sidecar = await startSidecar(
      { ...resolveSidecarCommand(app.getAppPath(), process.env), baseEnv: {} },
      realSidecarDeps()
    )
    proxy = createApiProxy({ baseUrl: sidecar.baseUrl, token: sidecar.token, fetchImpl: fetch })
    sidecarState = { ready: true }
  } catch (e) {
    sidecarState = { ready: false, error: e instanceof Error ? e.message : String(e) }
  }
}

function assertTrusted(frameUrl: string | undefined): void {
  if (!isTrustedSender(frameUrl ?? '', process.env['ELECTRON_RENDERER_URL']))
    throw new Error('untrusted sender')
}

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1100,
    minHeight: 700,
    show: false,
    title: 'UPSC JARVIS',
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: secureWebPreferences(join(__dirname, '../preload/index.js'))
  })

  mainWindow.on('ready-to-show', () => mainWindow.show())

  mainWindow.webContents.setWindowOpenHandler((details) => {
    if (isAllowedExternalUrl(details.url)) shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // The app never navigates away from its own origin.
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const current = mainWindow.webContents.getURL()
    if (url !== current && !url.startsWith(current.split('#')[0])) event.preventDefault()
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

app.whenReady().then(() => {
  electronApp.setAppUserModelId('com.upscjarvis.app')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  ipcMain.handle('api:request', async (event, req: ApiRequest) => {
    assertTrusted(event.senderFrame?.url)
    if (!proxy) return { status: 503, body: { error: 'sidecar-not-ready' } }
    return proxy(req)
  })
  ipcMain.handle('api:status', (event) => {
    assertTrusted(event.senderFrame?.url)
    return sidecarState
  })

  void bootSidecar()
  createWindow()

  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('before-quit', () => sidecar?.stop())

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
