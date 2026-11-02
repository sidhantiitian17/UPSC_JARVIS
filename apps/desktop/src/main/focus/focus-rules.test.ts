import { describe, expect, it } from 'vitest'
import { classifyWindow } from '@jarvis/shared'

describe('Focus Guard window classification', () => {
  it.each([
    [{ app: 'Adobe Acrobat', title: 'Laxmikanth.pdf' }, 'study'],
    [{ app: 'SumatraPDF', title: 'polity.pdf' }, 'study'],
    [{ app: 'Obsidian', title: 'Vault' }, 'study'],
    [{ app: 'Anki', title: 'Reviewing' }, 'study'],
    [{ app: 'Steam', title: 'Library' }, 'distraction'],
    [{ app: 'VALORANT', title: 'VALORANT' }, 'distraction'],
    [{ app: 'File Explorer', title: 'Downloads' }, 'neutral'],
    [{ app: 'Notepad', title: 'todo.txt' }, 'neutral']
  ])('%j is %s', (win, expected) => {
    expect(classifyWindow(win)).toBe(expected)
  })

  it('classifies a browser by the title keywords', () => {
    expect(classifyWindow({ app: 'Google Chrome', title: 'Instagram' })).toBe('distraction')
    expect(classifyWindow({ app: 'Microsoft Edge', title: 'Reels - Facebook' })).toBe('distraction')
    expect(classifyWindow({ app: 'Google Chrome', title: 'Drishti IAS - Polity notes' })).toBe(
      'study'
    )
    expect(classifyWindow({ app: 'Firefox', title: 'Inbox (3) - Gmail' })).toBe('neutral')
  })

  it('a study keyword wins over a distraction keyword in a browser title', () => {
    expect(classifyWindow({ app: 'Google Chrome', title: 'UPSC Polity lecture - YouTube' })).toBe(
      'study'
    )
  })

  it('does not treat a non-browser app as a distraction because of its title', () => {
    expect(classifyWindow({ app: 'Notepad', title: 'youtube ideas.txt' })).toBe('neutral')
  })

  it('ignores JARVIS and the OpenPets window', () => {
    expect(classifyWindow({ app: 'UPSC JARVIS', title: 'Today' })).toBeNull()
    expect(classifyWindow({ app: 'openpets', title: 'OpenPets Default Pet' })).toBeNull()
    expect(
      classifyWindow({
        app: 'electron',
        title: 'x',
        path: 'C:\\Users\\me\\AppData\\Local\\Programs\\openpets\\openpets.exe'
      })
    ).toBeNull()
  })

  it('returns only a category: no title leaks out', () => {
    const r = classifyWindow({ app: 'Google Chrome', title: 'Secret bank statement' })
    expect(r).toBe('neutral')
    expect(JSON.stringify(r)).not.toContain('Secret')
  })
})
