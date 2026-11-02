import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ApiError,
  answerGate,
  createGate,
  getProgress,
  finishGate,
  reportQuestion,
  skipGate,
  type Gate,
  type GateAnswer,
  type GateQuestion,
  type GateResult
} from '../api/client'
import { Button } from '../components/ui/button'
import { petEvent } from '../lib/pet'

export type GateClose = { openPage?: { documentId: number; page: number } } | undefined
type Props = { sessionId: number; documentId: number; onClose: (r?: GateClose) => void }
type Phase =
  | 'loading'
  | 'error'
  | 'choose'
  | 'confidence'
  | 'submitting'
  | 'feedback'
  | 'finishing'
  | 'result'
  | 'skipped'
type Confidence = 'G' | 'A' | 'R'

const CONFIDENCE: { key: Confidence; label: string; hint: string; tone: string }[] = [
  { key: 'G', label: 'Green', hint: 'sure', tone: 'border-success text-success' },
  { key: 'A', label: 'Amber', hint: '50-50', tone: 'border-warning text-warning' },
  { key: 'R', label: 'Red', hint: 'guess', tone: 'border-danger text-danger' }
]

function errorText(e: unknown): string {
  if (e instanceof ApiError) {
    const d = (e.body as { detail?: unknown } | null)?.detail
    if (typeof d === 'string') return d
  }
  return 'Something went wrong. Is the local service running?'
}

export function GateView({ sessionId, documentId, onClose }: Props): React.JSX.Element {
  const [phase, setPhase] = useState<Phase>('loading')
  const [gate, setGate] = useState<Gate | null>(null)
  const [questions, setQuestions] = useState<GateQuestion[]>([])
  const [index, setIndex] = useState(0)
  const [chosen, setChosen] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<GateAnswer | null>(null)
  const [result, setResult] = useState<GateResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [confirmSkip, setConfirmSkip] = useState(false)
  const [freeSkip, setFreeSkip] = useState(false)
  const shownAt = useRef(0)
  const levelBefore = useRef<number | null>(null)

  const current = questions[index]

  useEffect(() => {
    let alive = true
    getProgress()
      .then((g) => (levelBefore.current = g.level))
      .catch(() => undefined)
    createGate(sessionId)
      .then((g) => {
        if (!alive) return
        setGate(g)
        setQuestions(g.questions)
        shownAt.current = Date.now()
        setPhase('choose')
      })
      .catch((e) => {
        if (!alive) return
        setError(errorText(e))
        setPhase('error')
      })
    return () => {
      alive = false
    }
  }, [sessionId])

  const pick = useCallback((i: number) => {
    setChosen(i)
    setPhase('confidence')
  }, [])

  const submit = useCallback(
    async (confidence: Confidence) => {
      if (!current || chosen === null) return
      setPhase('submitting')
      try {
        setFeedback(
          await answerGate(sessionId, current.id, chosen, confidence, Date.now() - shownAt.current)
        )
        setPhase('feedback')
      } catch (e) {
        setError(errorText(e))
        setPhase('error')
      }
    },
    [current, chosen, sessionId]
  )

  const finish = useCallback(async () => {
    setPhase('finishing')
    try {
      const res = await finishGate(sessionId)
      setResult(res)
      setPhase('result')
      petEvent(res.passed ? 'gate_pass' : 'gate_not_passed', { retentionPct: res.retention_pct })
      if (res.passed && levelBefore.current !== null) {
        getProgress()
          .then((g) => {
            if (levelBefore.current !== null && g.level > levelBefore.current)
              petEvent('level_up', { level: g.level })
          })
          .catch(() => undefined)
      }
    } catch (e) {
      setError(errorText(e))
      setPhase('error')
    }
  }, [sessionId])

  const next = useCallback(() => {
    setChosen(null)
    setFeedback(null)
    if (index + 1 >= questions.length) {
      void finish()
      return
    }
    setIndex(index + 1)
    shownAt.current = Date.now()
    setPhase('choose')
  }, [index, questions.length, finish])

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (confirmSkip) return
      const tag = (e.target as HTMLElement | null)?.tagName
      if (tag === 'INPUT' && (e.target as HTMLInputElement).type !== 'radio') return
      if ((phase === 'choose' || phase === 'confidence') && /^[1-4]$/.test(e.key)) {
        pick(Number(e.key) - 1)
      } else if (phase === 'confidence') {
        const c = CONFIDENCE.find((x) => x.key.toLowerCase() === e.key.toLowerCase())
        if (c) void submit(c.key)
      } else if (phase === 'feedback' && (e.key === 'Enter' || e.key === ' ')) {
        e.preventDefault()
        next()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, confirmSkip, pick, submit, next])

  const report = async (): Promise<void> => {
    if (!current) return
    try {
      await reportQuestion(current.id)
      const rest = questions.filter((q) => q.id !== current.id)
      setQuestions(rest)
      setChosen(null)
      if (rest.length === 0) {
        setError('No questions are left in this gate.')
        setPhase('error')
      } else {
        setIndex(Math.min(index, rest.length - 1))
        shownAt.current = Date.now()
        setPhase('choose')
      }
    } catch (e) {
      setError(errorText(e))
      setPhase('error')
    }
  }

  // The gate could not be built at all, so leaving it is free (no double-gate penalty).
  const skipUnbuilt = async (): Promise<void> => {
    try {
      setResult(await skipGate(sessionId, false))
      setFreeSkip(true)
      setPhase('skipped')
    } catch (e) {
      setError(errorText(e))
    }
  }

  const skip = async (): Promise<void> => {
    setConfirmSkip(false)
    try {
      setResult(await skipGate(sessionId))
      setPhase('skipped')
    } catch (e) {
      setError(errorText(e))
      setPhase('error')
    }
  }

  const answering =
    phase === 'choose' || phase === 'confidence' || phase === 'submitting' || phase === 'feedback'

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Recall gate"
      className="fixed inset-0 z-50 flex flex-col overflow-auto bg-app-bg p-8"
    >
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Recall gate</h1>
          {answering && current && (
            <span className="text-sm text-muted">
              Question {index + 1} of {questions.length}
            </span>
          )}
        </header>

        {phase === 'loading' && <p role="status">Building your recall questions…</p>}

        {phase === 'error' && (
          <div className="flex flex-col items-start gap-3">
            <div role="alert" className="rounded-lg border border-danger p-3 text-danger">
              {error}
            </div>
            <div className="flex gap-2">
              {!gate && <Button onClick={() => void skipUnbuilt()}>Skip this gate</Button>}
              <Button onClick={() => onClose()}>Close</Button>
            </div>
          </div>
        )}

        {gate?.fallback_used && answering && (
          <p className="rounded-lg border border-warning p-2 text-sm text-warning">
            This quiz was built offline from your text because no AI service was reachable.
          </p>
        )}
        {gate?.short_range && answering && (
          <p className="text-sm text-muted">
            The range you read was short, so this gate has fewer questions than usual.
          </p>
        )}

        {answering && current && (
          <section aria-label="Question" className="flex flex-col gap-4">
            <p className="text-xl">{current.stem}</p>
            {current.interleaved && (
              <p className="text-xs text-muted">Review question from earlier reading</p>
            )}
            <div role="radiogroup" aria-label="Options" className="flex flex-col gap-2">
              {current.options.map((opt, i) => (
                <label
                  key={i}
                  className="flex min-h-12 cursor-pointer items-center gap-3 rounded-lg border border-line p-3 has-[:checked]:border-info"
                >
                  <input
                    type="radio"
                    name="option"
                    checked={chosen === i}
                    disabled={phase === 'submitting' || phase === 'feedback'}
                    onChange={() => pick(i)}
                    aria-label={opt}
                  />
                  <span className="text-muted">{i + 1}</span>
                  <span>{opt}</span>
                </label>
              ))}
            </div>

            {phase === 'confidence' && (
              <div role="group" aria-label="How sure are you?" className="flex items-center gap-2">
                <span className="text-sm text-muted">How sure are you?</span>
                {CONFIDENCE.map((c) => (
                  <button
                    key={c.key}
                    type="button"
                    aria-label={`${c.label}: ${c.hint}`}
                    onClick={() => void submit(c.key)}
                    className={`min-h-10 rounded-lg border px-4 font-semibold ${c.tone}`}
                  >
                    {c.key}
                    <span className="ml-2 text-xs font-normal">{c.hint}</span>
                  </button>
                ))}
              </div>
            )}

            {phase === 'feedback' && feedback && (
              <div className="flex flex-col gap-3 rounded-lg border border-line p-4">
                <p data-testid="verdict" className="font-semibold">
                  {feedback.correct
                    ? '✓ Correct'
                    : `✕ Incorrect. Correct answer: ${current.options[feedback.answer_index]}`}
                </p>
                {feedback.explanation && <p>{feedback.explanation}</p>}
                <blockquote className="border-l-2 border-line pl-3 text-sm text-muted">
                  “{feedback.source_quote}”
                  <footer>
                    Source: page {feedback.page}, paragraph {(feedback.ordinal ?? 0) + 1}
                  </footer>
                </blockquote>
                <Button variant="primary" onClick={next}>
                  {index + 1 >= questions.length ? 'See result' : 'Next question'}
                </Button>
              </div>
            )}

            {phase !== 'feedback' && (
              <div className="flex items-center gap-3 pt-2">
                <Button onClick={() => void report()}>Report bad question</Button>
                <Button onClick={() => setConfirmSkip(true)}>Emergency skip</Button>
              </div>
            )}
          </section>
        )}

        {phase === 'finishing' && <p role="status">Scoring…</p>}

        {phase === 'result' && result && (
          <section
            aria-label="Gate result"
            className="flex flex-col gap-4 rounded-card border border-line p-6"
          >
            <p className="text-4xl font-semibold">{result.retention_pct}%</p>
            <p className="text-sm text-muted">
              retention · {result.correct} of {result.total} correct · pass mark {result.pass_mark}%
            </p>
            <h2 className="text-xl font-semibold">{result.passed ? 'Passed' : 'Not passed'}</h2>
            {result.passed ? (
              <>
                <p>+{result.xp} XP for verified retained minutes.</p>
                {result.nodes.length > 0 && (
                  <div>
                    <p className="text-sm text-muted">Coverage added for:</p>
                    <ul className="mt-1 flex flex-wrap gap-1">
                      {result.nodes.map((n) => (
                        <li key={n.id} className="rounded border border-line px-1.5 text-sm">
                          {n.title}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <>
                <p>Coverage did not increase. Revisit these parts, then try again:</p>
                <ul className="flex flex-col gap-3">
                  {result.restudy.map((r) => (
                    <li
                      key={r.chunk_id}
                      className="flex items-start justify-between gap-4 rounded-lg border border-line p-3"
                    >
                      <div>
                        <span className="font-semibold">
                          {r.book} · page {r.page}, paragraph {r.ordinal + 1}
                        </span>
                        <p className="text-sm text-muted">“{r.quote}”</p>
                      </div>
                      <Button
                        aria-label={`Review page ${r.page}`}
                        onClick={() => onClose({ openPage: { documentId, page: r.page } })}
                      >
                        Open in reader
                      </Button>
                    </li>
                  ))}
                </ul>
              </>
            )}
            <Button variant="primary" onClick={() => onClose()}>
              Done
            </Button>
          </section>
        )}

        {phase === 'skipped' && (
          <section
            aria-label="Gate skipped"
            className="flex flex-col items-start gap-3 rounded-card border border-line p-6"
          >
            <h2 className="text-xl font-semibold">Gate skipped</h2>
            <p>
              {freeSkip
                ? 'No coverage or XP was awarded. There is no penalty because the questions could not be built.'
                : 'No coverage or XP was awarded, and tomorrow\u2019s gate will have double the questions.'}
            </p>
            <Button variant="primary" onClick={() => onClose()}>
              Close
            </Button>
          </section>
        )}
      </div>

      {confirmSkip && (
        <div
          role="alertdialog"
          aria-label="Confirm emergency skip"
          className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-6"
        >
          <div className="flex max-w-md flex-col gap-4 rounded-card bg-surface p-6">
            <p>
              Skip this gate? No coverage or XP is awarded, and tomorrow&apos;s gate will have
              double the questions.
            </p>
            <div className="flex gap-2">
              <Button variant="primary" onClick={() => void skip()}>
                Skip anyway
              </Button>
              <Button onClick={() => setConfirmSkip(false)}>Keep going</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
