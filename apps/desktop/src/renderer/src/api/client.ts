import type { ApiMethod, components } from '@jarvis/shared'

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown
  ) {
    super(`API error ${status}`)
  }
}

/** The sidecar needs a few seconds to boot; screens that open at launch wait instead of failing. */
export const startupRetry = { tries: 60, delayMs: 500 }

const notReady = (res: { status: number; body: unknown }): boolean =>
  res.status === 503 && (res.body as { error?: string } | null)?.error === 'sidecar-not-ready'

/** Calls the sidecar through the preload bridge (main adds the token). */
export async function api<T>(method: ApiMethod, path: string, body?: unknown): Promise<T> {
  let res = await window.jarvis.api({ method, path, body })
  for (let i = 0; i < startupRetry.tries && notReady(res); i++) {
    await new Promise((r) => setTimeout(r, startupRetry.delayMs))
    res = await window.jarvis.api({ method, path, body })
  }
  if (res.status < 200 || res.status >= 300) throw new ApiError(res.status, res.body)
  return res.body as T
}

export const getHealth = (): Promise<components['schemas']['Health']> => api('GET', '/health')

type Schemas = components['schemas']

export const getSettings = (): Promise<Schemas['SettingsOut']> => api('GET', '/settings')
export const putSettings = (body: Schemas['SettingsIn']): Promise<Schemas['SettingsOut']> =>
  api('PUT', '/settings', body)
export const testAi = (): Promise<Schemas['AiTestOut']> => api('POST', '/llm/test')

export type SyllabusNode = Schemas['SyllabusNodeOut']
export const getSyllabusTree = (): Promise<SyllabusNode[]> => api('GET', '/syllabus/tree')
export const reloadSyllabus = (): Promise<Schemas['ReloadOut']> => api('POST', '/syllabus/reload')

export type LibraryDocument = Schemas['DocumentOut']
export type AddDocumentResult = Schemas['AddDocumentOut']
export type SearchHit = Schemas['SearchHit']
export const listDocuments = (): Promise<LibraryDocument[]> => api('GET', '/library/documents')
export const addDocument = (path: string): Promise<AddDocumentResult> =>
  api('POST', '/library/documents', { path })
export const searchLibrary = (q: string): Promise<SearchHit[]> =>
  api('GET', `/library/search?q=${encodeURIComponent(q)}`)

export const getDocumentInfo = (id: number): Promise<LibraryDocument> =>
  api('GET', `/library/documents/${id}`)
export const getDocumentFile = (id: number): Promise<{ contentType: string; base64: string }> =>
  api('GET', `/library/documents/${id}/file`)
export const savePosition = (id: number, page: number): Promise<LibraryDocument> =>
  api('PUT', `/library/documents/${id}/position`, { page })

export type StudySession = Schemas['SessionOut']
export type ChunkInfo = Schemas['ChunkOut']
export const listChunks = (docId: number, page: number): Promise<ChunkInfo[]> =>
  api('GET', `/library/documents/${docId}/pages/${page}/chunks`)
export const getActiveSession = (): Promise<StudySession | null> => api('GET', '/sessions/active')
export const startSession = (document_id: number, start_chunk_id: number): Promise<StudySession> =>
  api('POST', '/sessions', { document_id, start_chunk_id })
export const endSession = (
  id: number,
  end_chunk_id: number,
  focused_seconds?: number
): Promise<StudySession> => api('POST', `/sessions/${id}/end`, { end_chunk_id, focused_seconds })
export const cancelSession = (id: number): Promise<StudySession> =>
  api('POST', `/sessions/${id}/cancel`)
export const setSessionTags = (id: number, node_ids: string[]): Promise<StudySession> =>
  api('PUT', `/sessions/${id}/tags`, { node_ids })

export type Gate = Schemas['GateOut']
export type GateQuestion = Schemas['GateQuestion']
export type GateAnswer = Schemas['AnswerOut']
export type GateResult = Schemas['ResultOut']
export const createGate = (sessionId: number): Promise<Gate> =>
  api('POST', `/sessions/${sessionId}/gate`)
export const answerGate = (
  sessionId: number,
  question_id: number,
  chosen_index: number,
  confidence: 'G' | 'A' | 'R',
  time_ms?: number
): Promise<GateAnswer> =>
  api('POST', `/sessions/${sessionId}/gate/answer`, {
    question_id,
    chosen_index,
    confidence,
    time_ms
  })
export const finishGate = (sessionId: number): Promise<GateResult> =>
  api('POST', `/sessions/${sessionId}/gate/finish`)
export const skipGate = (sessionId: number, penalty = true): Promise<GateResult> =>
  api('POST', `/sessions/${sessionId}/gate/skip`, { penalty })
export const reportQuestion = (questionId: number, reason = ''): Promise<unknown> =>
  api('POST', `/questions/${questionId}/report`, { reason })
export const getAwaitingGate = (): Promise<StudySession | null> =>
  api('GET', '/sessions/awaiting-gate')

export type ReviewCard = Schemas['ReviewCard']
export type ReviewStats = Schemas['ReviewStats']
export const getReviewQueue = (): Promise<ReviewCard[]> => api('GET', '/review/queue')
export const getReviewStats = (): Promise<ReviewStats> => api('GET', '/review/stats')
export const rateReviewCard = (
  cardId: number,
  rating: 1 | 2 | 3 | 4
): Promise<Schemas['RateOut']> => api('POST', `/review/cards/${cardId}/rate`, { rating })

export type NodeCoverage = Schemas['NodeCoverage']
export type TodayDashboard = Schemas['TodayOut']
export const getCoverage = (): Promise<NodeCoverage[]> => api('GET', '/coverage/nodes')
export const getToday = (): Promise<TodayDashboard> => api('GET', '/dashboard/today')

export type GameProgress = Schemas['ProgressOut']
export const getProgress = (): Promise<GameProgress> => api('GET', '/gamification/progress')

export type GuardStatus = Schemas['GuardOut']
export const getGuard = (): Promise<GuardStatus> => api('GET', '/guard/status')
export const setBadDay = (active: boolean): Promise<GuardStatus> =>
  api('PUT', '/guard/bad-day', { active })

export type DayPlan = Schemas['PlanOut']
export type PlannerStatus = Schemas['StatusOut']
export const makePlan = (free_hours: number): Promise<DayPlan> =>
  api('POST', '/planner/plan', { free_hours })
export const commitPlan = (free_hours: number): Promise<Schemas['Committed']> =>
  api('POST', '/planner/commit', { free_hours })
export const getPlannerStatus = (): Promise<PlannerStatus> => api('GET', '/planner/status')

export type Truth = Schemas['TruthOut']
export const getTruth = (): Promise<Truth> => api('GET', '/insights/truth')
