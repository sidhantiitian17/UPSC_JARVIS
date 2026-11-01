// @vitest-environment node
import { describe, expect, it } from 'vitest'
import { isTrustedSender } from './trusted-sender'

describe('isTrustedSender', () => {
  it('accepts the dev server origin and our own file:// bundle only', () => {
    expect(isTrustedSender('http://localhost:5173/#/today', 'http://localhost:5173')).toBe(true)
    expect(isTrustedSender('file:///app/out/renderer/index.html#/study', undefined)).toBe(true)
  })
  it('rejects other origins and malformed urls', () => {
    for (const u of [
      'https://evil.example/',
      'http://localhost:9999/',
      'javascript:1',
      'garbage',
      ''
    ])
      expect(isTrustedSender(u, 'http://localhost:5173')).toBe(false)
  })
})
