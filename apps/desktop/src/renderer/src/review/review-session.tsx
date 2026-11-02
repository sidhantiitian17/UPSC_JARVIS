import { useCallback, useEffect, useState } from 'react'
import { getReviewQueue, rateReviewCard, type ReviewCard } from '../api/client'
import { Button } from '../components/ui/button'

type Phase = 'loading' | 'error' | 'empty' | 'question' | 'rate' | 'done'
const RATINGS = [
  { value: 1, label: 'Again', hint: 'forgot' },
  { value: 2, label: 'Hard', hint: 'struggled' },
  { value: 3, label: 'Good', hint: 'recalled' },
  { value: 4, label: 'Easy', hint: 'instant' }
] as const

export function ReviewSession({ onClose }: { onClose: () => void }): React.JSX.Element {
  const [phase, setPhase] = useState<Phase>('loading')
  const [cards, setCards] = useState<ReviewCard[]>([])
  const [index, setIndex] = useState(0)
  const [chosen, setChosen] = useState<number | null>(null)
  const [reviewed, setReviewed] = useState(0)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let alive = true
    getReviewQueue()
      .then((q) => {
        if (!alive) return
        setCards(q)
        setPhase(q.length ? 'question' : 'empty')
      })
      .catch(() => {
        if (!alive) return
        setError('Could not load your review cards. Is the local service running?')
        setPhase('error')
      })
    return () => {
      alive = false
    }
  }, [])

  const card = cards[index]

  const rate = useCallback(
    async (rating: 1 | 2 | 3 | 4) => {
      if (!card) return
      try {
        await rateReviewCard(card.card_id, rating)
      } catch {
        setError('Could not save that rating. Try again.')
        return
      }
      setError(null)
      setReviewed((n) => n + 1)
      setChosen(null)
      if (index + 1 >= cards.length) setPhase('done')
      else {
        setIndex(index + 1)
        setPhase('question')
      }
    },
    [card, index, cards.length]
  )

  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (!/^[1-4]$/.test(e.key)) return
      const n = Number(e.key)
      if (phase === 'question') {
        setChosen(n - 1)
        setPhase('rate')
      } else if (phase === 'rate') void rate(n as 1 | 2 | 3 | 4)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [phase, rate])

  return (
    <section aria-label="Review" className="mx-auto flex max-w-3xl flex-col gap-6">
      <header className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Review</h2>
        {(phase === 'question' || phase === 'rate') && (
          <span className="text-sm text-muted">
            Card {index + 1} of {cards.length}
          </span>
        )}
      </header>

      {phase === 'loading' && <p role="status">Loading your cards…</p>}
      {error && (
        <div role="alert" className="rounded-lg border border-danger p-3 text-sm text-danger">
          {error}
        </div>
      )}
      {(phase === 'error' || phase === 'empty') && (
        <div className="flex flex-col items-start gap-3">
          {phase === 'empty' && <p>Nothing is due right now. Come back after your next gate.</p>}
          <Button onClick={onClose}>Back</Button>
        </div>
      )}

      {(phase === 'question' || phase === 'rate') && card && (
        <div className="flex flex-col gap-4">
          <p className="text-xl">{card.stem}</p>
          <div role="radiogroup" aria-label="Options" className="flex flex-col gap-2">
            {card.options.map((opt, i) => (
              <label
                key={i}
                className="flex min-h-12 cursor-pointer items-center gap-3 rounded-lg border border-line p-3 has-[:checked]:border-info"
              >
                <input
                  type="radio"
                  name="review-option"
                  aria-label={opt}
                  checked={chosen === i}
                  disabled={phase === 'rate'}
                  onChange={() => {
                    setChosen(i)
                    setPhase('rate')
                  }}
                />
                <span className="text-muted">{i + 1}</span>
                <span>{opt}</span>
              </label>
            ))}
          </div>

          {phase === 'rate' && chosen !== null && (
            <div className="flex flex-col gap-3 rounded-lg border border-line p-4">
              <p data-testid="verdict" className="font-semibold">
                {chosen === card.answer_index
                  ? '✓ Correct'
                  : `✕ Incorrect. Correct answer: ${card.options[card.answer_index]}`}
              </p>
              {card.explanation && <p>{card.explanation}</p>}
              <blockquote className="border-l-2 border-line pl-3 text-sm text-muted">
                “{card.source_quote}”
              </blockquote>
              <div
                role="group"
                aria-label="How well did you remember?"
                className="flex flex-wrap items-center gap-2"
              >
                {RATINGS.map((r) => (
                  <Button
                    key={r.value}
                    variant={r.value === 3 ? 'primary' : undefined}
                    onClick={() => void rate(r.value)}
                  >
                    {r.label}
                    <span className="ml-2 text-xs opacity-70">
                      {r.value} · {r.hint}
                    </span>
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {phase === 'done' && (
        <div className="flex flex-col items-start gap-3">
          <p className="text-xl">
            {reviewed} {reviewed === 1 ? 'card' : 'cards'} reviewed. Nice work.
          </p>
          <Button variant="primary" onClick={onClose}>
            Done
          </Button>
        </div>
      )}
    </section>
  )
}
