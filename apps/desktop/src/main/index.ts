import { app, shell, BrowserWindow, ipcMain, safeStorage, dialog } from 'electron'
import { existsSync } from 'fs'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import type { ApiRequest, SidecarState } from '@jarvis/shared'
import { createApiProxy } from './api-proxy'
import { createSecretStore } from './secret-store'
import { resolveSidecarCommand, startSidecar, type RunningSidecar } from './sidecar'
import { realSidecarDeps } from './sidecar-runtime'
import { isTrustedSender } from './trusted-sender'
import { isAllowedExternalUrl, secureWebPreferences } from './window-options'

let sidecar: RunningSidecar | null = null
let proxy: ReturnType<typeof createApiProxy> | null = null
let sidecarState: SidecarState = { ready: false }
let secretStore: ReturnType<typeof createSecretStore> | null = null

async function pushSecretsToSidecar(): Promise<void> {
  if (!proxy || !secretStore) return
  for (const [name, value] of Object.entries(secretStore.getAll())) {
    try {
      await proxy({ method: 'PUT', path: `/secrets/${name}`, body: { value } })
    } catch {
      /* a stale or rejected secret must not stop the app */
    }
  }
}

async function bootSidecar(): Promise<void> {
  try {
    const baseEnv: Record<string, string> = { JARVIS_DATA_DIR: app.getPath('userData') }
    const routing = join(app.getAppPath(), '..', '..', 'config', 'routing.yaml')
    if (existsSync(routing)) baseEnv.JARVIS_ROUTING = routing
    sidecar = await startSidecar(
      { ...resolveSidecarCommand(app.getAppPath(), process.env), baseEnv },
      realSidecarDeps()
    )
    proxy = createApiProxy({ baseUrl: sidecar.baseUrl, token: sidecar.token, fetchImpl: fetch })
    await pushSecretsToSidecar()
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

  secretStore = createSecretStore({ dir: app.getPath('userData'), safeStorage })

  ipcMain.handle('secrets:set', async (event, name: string, value: string) => {
    assertTrusted(event.senderFrame?.url)
    if (!secretStore) throw new Error('secret store not ready')
    secretStore.set(name, value)
    if (proxy) {
      const res = await proxy({ method: 'PUT', path: `/secrets/${name}`, body: { value } })
      if (res.status >= 400) {
        secretStore.delete(name)
        throw new Error(`sidecar rejected the secret (HTTP ${res.status})`)
      }
    }
  })
  ipcMain.handle('secrets:delete', async (event, name: string) => {
    assertTrusted(event.senderFrame?.url)
    secretStore?.delete(name)
    if (proxy) await proxy({ method: 'DELETE', path: `/secrets/${name}` })
  })
  ipcMain.handle('secrets:names', (event) => {
    assertTrusted(event.senderFrame?.url)
    return secretStore?.names() ?? []
  })
  ipcMain.handle('dialog:pickFolder', async (event) => {
    assertTrusted(event.senderFrame?.url)
    const win = BrowserWindow.fromWebContents(event.sender)
    const opts = {
      properties: ['openDirectory', 'createDirectory'] as ('openDirectory' | 'createDirectory')[]
    }
    const res = win ? await dialog.showOpenDialog(win, opts) : await dialog.showOpenDialog(opts)
    return res.canceled ? null : (res.filePaths[0] ?? null)
  })

  ipcMain.handle('dialog:pickPdf', async (event) => {
    assertTrusted(event.senderFrame?.url)
    const win = BrowserWindow.fromWebContents(event.sender)
    const opts = {
      properties: ['openFile'] as 'openFile'[],
      filters: [{ name: 'PDF documents', extensions: ['pdf'] }]
    }
    const res = win ? await dialog.showOpenDialog(win, opts) : await dialog.showOpenDialog(opts)
    return res.canceled ? null : (res.filePaths[0] ?? null)
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
