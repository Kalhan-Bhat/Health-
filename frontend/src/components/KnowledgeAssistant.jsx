import { useEffect, useMemo, useRef, useState } from 'react'
import { Send, MessageCircleQuestion } from 'lucide-react'
import ChatMessage from './ChatMessage.jsx'
import LoadingState from './LoadingState.jsx'
import { askQuestion } from '../api/client.js'
import { MAX_HISTORY_TURNS, MAX_QUESTION_CHARS, SUGGESTED_QUESTIONS } from '../utils/constants.js'
import { isAbnormal } from '../utils/format.js'
import { buildReportContext } from '../utils/chat.js'

// Show similarity scores on source cards when the page URL contains ?debug
const DEBUG =
  typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('debug')

/** Last N turns as plain {role, content} pairs, used only for follow-up phrasing. */
function buildHistory(messages) {
  return messages
    .filter((m) => !m.error)
    .slice(-MAX_HISTORY_TURNS)
    .map((m) => ({
      role: m.role,
      content: (m.role === 'user' ? m.content : m.response.answer).slice(0, 2000),
    }))
}

/**
 * Feature F2: chat with the knowledge base. Answers come with numbered citations
 * and source cards. If a report has been analysed, the user can let the assistant
 * use it ("Use my report for context").
 *
 * @param {{ report: object|null, messages: object[], setMessages: Function }} props
 */
export default function KnowledgeAssistant({ report, messages, setMessages }) {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [useReport, setUseReport] = useState(true)
  const listEndRef = useRef(null)

  useEffect(() => {
    listEndRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  // Static suggestions, plus "What is X?" for each out-of-range test in the report.
  const suggestions = useMemo(() => {
    const dynamic = report ? report.tests.filter(isAbnormal).map((t) => `What is ${t.name}?`) : []
    return [...dynamic.slice(0, 4), ...SUGGESTED_QUESTIONS]
  }, [report])

  const lastFollowUps = useMemo(() => {
    const last = messages[messages.length - 1]
    return last?.role === 'assistant' && !last.error ? last.response.follow_up_suggestions : []
  }, [messages])

  async function send(question) {
    const q = question.trim()
    if (q.length < 3 || loading) return
    const history = buildHistory(messages)
    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setLoading(true)
    const payload = { question: q, history }
    if (report && useReport) payload.report_context = buildReportContext(report)
    try {
      const response = await askQuestion(payload)
      setMessages((m) => [...m, { role: 'assistant', response }])
    } catch (error) {
      setMessages((m) => [...m, { role: 'assistant', error, retryQuestion: q }])
    } finally {
      setLoading(false)
    }
  }

  function retry(message) {
    // Remove the failed answer and its question, then ask again.
    setMessages((m) => m.slice(0, -2))
    send(message.retryQuestion)
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send(input)
    }
  }

  return (
    <section className="card assistant" aria-labelledby="ask-title">
      <div className="section-header">
        <h1 id="ask-title">Ask about lab tests</h1>
        {report && (
          <label className="toggle">
            <input
              type="checkbox"
              checked={useReport}
              onChange={(e) => setUseReport(e.target.checked)}
            />
            <span>Use my report for context</span>
          </label>
        )}
      </div>
      <p className="muted small">
        Answers come only from MedBridge&apos;s curated knowledge base, with sources. MedBridge does
        not diagnose or give treatment advice.
      </p>

      <div className="chat-log" aria-live="polite">
        {messages.length === 0 && (
          <div className="chat-empty">
            <MessageCircleQuestion size={36} aria-hidden="true" />
            <p>Ask a question about a test or a medical term, or try one of these:</p>
          </div>
        )}
        {messages.map((m, i) => (
          <ChatMessage
            key={i}
            message={m}
            index={i}
            debug={DEBUG}
            onRetry={m.error ? () => retry(m) : undefined}
          />
        ))}
        {loading && <LoadingState messages={['Searching the knowledge base…']} />}
        <div ref={listEndRef} />
      </div>

      <div className="chips" aria-label="Suggested questions">
        {(lastFollowUps.length ? lastFollowUps : suggestions).map((s) => (
          <button key={s} type="button" className="chip" disabled={loading} onClick={() => send(s)}>
            {s}
          </button>
        ))}
      </div>

      <form
        className="chat-input"
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
      >
        <label htmlFor="question" className="visually-hidden">
          Your question
        </label>
        <textarea
          id="question"
          rows={2}
          value={input}
          maxLength={MAX_QUESTION_CHARS}
          placeholder="e.g. What does MCV mean?"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <div className="chat-input__footer">
          <span className="small muted">
            {input.length}/{MAX_QUESTION_CHARS} · Enter to send, Shift+Enter for a new line
          </span>
          <button
            type="submit"
            className="btn btn--primary"
            disabled={loading || input.trim().length < 3}
          >
            <Send size={16} aria-hidden="true" /> Ask
          </button>
        </div>
      </form>
    </section>
  )
}
