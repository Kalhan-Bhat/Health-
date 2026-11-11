import { useEffect, useState } from 'react'

/**
 * Spinner with optional staged messages that change every few seconds.
 * The stages are cosmetic — they are timed, not real progress.
 * @param {{ messages?: string[], intervalMs?: number }} props
 */
export default function LoadingState({ messages = ['Loading…'], intervalMs = 3500 }) {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    if (messages.length < 2) return undefined
    const id = setInterval(() => setIndex((i) => Math.min(i + 1, messages.length - 1)), intervalMs)
    return () => clearInterval(id)
  }, [messages, intervalMs])

  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="spinner" aria-hidden="true" />
      <p>{messages[index]}</p>
    </div>
  )
}
