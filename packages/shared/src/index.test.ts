import { describe, expect, it } from 'vitest'
import { APP_NAME, SCREENS } from './index'

describe('shared constants', () => {
  it('names the app and lists ten unique screens', () => {
    expect(APP_NAME).toBe('UPSC JARVIS')
    expect(SCREENS).toHaveLength(10)
    expect(new Set(SCREENS).size).toBe(10)
  })
})
