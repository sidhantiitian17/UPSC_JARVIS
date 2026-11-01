import {
  BookOpen,
  Brain,
  Compass,
  FileQuestion,
  Globe,
  LineChart,
  Mic,
  Newspaper,
  PenLine,
  Settings,
  type LucideIcon
} from 'lucide-react'
import type { ScreenId } from '@jarvis/shared'

export type ScreenMeta = {
  label: string
  icon: LucideIcon
  description: string
  emptyTitle: string
  emptyBody: string
  primaryAction: string
}

/** Copy and icon for every screen. Keys must cover every id in @jarvis/shared SCREENS. */
export const SCREEN_META: Record<ScreenId, ScreenMeta> = {
  today: {
    label: 'Today',
    icon: Compass,
    description: 'Your next block, due cards and honest progress.',
    emptyTitle: 'Nothing planned yet',
    emptyBody: 'Add a PDF to your library and start a focus block. Your day will appear here.',
    primaryAction: 'Start a study block'
  },
  study: {
    label: 'Study',
    icon: BookOpen,
    description: 'Library, reader, bookmarks and the focus timer.',
    emptyTitle: 'Your library is empty',
    emptyBody: 'Add a PDF, set a start bookmark, read, and finish with the recall gate.',
    primaryAction: 'Add a PDF'
  },
  syllabus: {
    label: 'Syllabus',
    icon: Brain,
    description: 'Coverage by micro-theme. Progress rises only when recall passes.',
    emptyTitle: 'No syllabus loaded',
    emptyBody: 'Load the syllabus tree to track coverage down to micro-themes.',
    primaryAction: 'Load syllabus'
  },
  pyq: {
    label: 'PYQ Lab',
    icon: FileQuestion,
    description: 'Previous-year questions, traps and mistake autopsy.',
    emptyTitle: 'No questions imported',
    emptyBody: 'Import the verified PYQ dataset to start drills and trend analysis.',
    primaryAction: 'Import PYQs'
  },
  mains: {
    label: 'Mains',
    icon: PenLine,
    description: 'Answer writing, rubric evaluation and handwriting practice.',
    emptyTitle: 'No answers evaluated',
    emptyBody: 'Write or upload an answer to get rubric-based feedback.',
    primaryAction: 'Write an answer'
  },
  ca: {
    label: 'Current Affairs',
    icon: Newspaper,
    description: 'Daily digest linked to your static syllabus.',
    emptyTitle: 'No digest yet',
    emptyBody: 'Fetch today’s public sources to build your 35-minute digest.',
    primaryAction: 'Fetch today’s digest'
  },
  interview: {
    label: 'Interview',
    icon: Mic,
    description: 'Silent mock interview with a practice score.',
    emptyTitle: 'No interview recorded',
    emptyBody: 'Fill your DAF and start a silent mock. Video is not stored by default.',
    primaryAction: 'Start a mock interview'
  },
  browser: {
    label: 'Focus Browser',
    icon: Globe,
    description: 'Ad-free, Shorts-free lectures from your allowlist.',
    emptyTitle: 'No lectures allowed yet',
    emptyBody: 'Add the channels you trust. Everything else stays blocked.',
    primaryAction: 'Add a channel'
  },
  insights: {
    label: 'Insights',
    icon: LineChart,
    description: 'Verified retained minutes, calibration and forecasts.',
    emptyTitle: 'Not enough data',
    emptyBody: 'Complete a few sessions with recall gates to see your real numbers.',
    primaryAction: 'Start a study block'
  },
  settings: {
    label: 'Settings',
    icon: Settings,
    description: 'AI providers, folders and privacy.',
    emptyTitle: 'Nothing configured',
    emptyBody: 'Choose your library and vault folders and connect a free AI provider.',
    primaryAction: 'Open setup'
  }
}
