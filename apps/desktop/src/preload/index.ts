import { contextBridge } from 'electron'

// Minimal, sandbox-safe bridge. API access (base URL + token) is added in WU-P01-003.
contextBridge.exposeInMainWorld('jarvis', { platform: process.platform })
