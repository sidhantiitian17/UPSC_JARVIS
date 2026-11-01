/**
 * Design tokens from agents/project/DESIGN.md. main.css must contain the same values
 * (enforced by tokens.test.ts). `accentContrast` is the text colour used ON the accent colour.
 */
export const tokens = {
  dark: {
    bg: '#0F1220',
    surface: '#171B2E',
    surface2: '#1F2440',
    text: '#E8EAF2',
    textMuted: '#9AA1BD',
    accent: '#F4A340',
    accentContrast: '#0F1220',
    info: '#6C7CFF',
    success: '#3FB68B',
    warning: '#E5B13A',
    danger: '#E5645B'
  },
  light: {
    bg: '#FAF7F2',
    surface: '#FFFFFF',
    surface2: '#F1ECE3',
    text: '#1B1E2B',
    textMuted: '#5B6178',
    accent: '#C97A12',
    accentContrast: '#1B1E2B',
    info: '#4553D6',
    success: '#1F8A64',
    warning: '#A87A0E',
    danger: '#C23A31'
  }
} as const
