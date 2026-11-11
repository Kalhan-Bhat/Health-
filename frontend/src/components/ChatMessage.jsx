import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { SearchX } from 'lucide-react'
import SourceCard from './SourceCard.jsx'
import ErrorState from './ErrorState.jsx'
import { linkCitations } from '../utils/chat.js'

/**
 * One chat bubble. User messages are plain text; assistant messages render markdown,
 * citation superscripts that jump to the matching source card, and the source list.
 *
 * @param {{ message: object, index: number, debug?: boolean, onRetry?: () => void }} props
 */
export default function ChatMessage({ message, index, debug = false, onRetry }) {
  const [highlighted, setHighlighted] = useState(null)

  if (message.role === 'user') {
    return (
      <div className="chat-message chat-message--user">
        <p>{message.content}</p>
      </div>
    )
  }

  if (message.error) {
    return (
      <div className="chat-message chat-message--assistant">
        <ErrorState error={message.error} onRetry={onRetry} />
      </div>
    )
  }

  const res = message.response
  const anchor = (n) => `src-${index}-${n}`
  const sourceIds = new Set(res.sources.map((s) => s.id))

  function jumpToSource(n) {
    document.getElementById(anchor(n))?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    setHighlighted(n)
    setTimeout(() => setHighlighted(null), 1800)
  }

  // Custom renderer for links: citations become buttons, real links open in a new tab.
  const components = {
    a({ href, children }) {
      if (href?.startsWith('#cite-')) {
        const n = Number(href.slice(6))
        if (!sourceIds.has(n)) return <sup className="citation citation--plain">[{n}]</sup>
        return (
          <sup>
            <button
              type="button"
              className="citation"
              onClick={() => jumpToSource(n)}
              aria-label={`Show source ${n}`}
            >
              {n}
            </button>
          </sup>
        )
      }
      if (href === '#report') {
        return (
          <span className="report-badge" title="From your own report">
            your report
          </span>
        )
      }
      return (
        <a href={href} target="_blank" rel="noopener noreferrer">
          {children}
        </a>
      )
    },
  }

  return (
    <div className="chat-message chat-message--assistant">
      {!res.grounded && (
        <span className="kb-badge">
          <SearchX size={14} aria-hidden="true" /> Not found in knowledge base
        </span>
      )}
      <div className="chat-markdown">
        <ReactMarkdown components={components}>{linkCitations(res.answer)}</ReactMarkdown>
      </div>

      {res.sources.length > 0 && (
        <div className="sources">
          <p className="sources__label small">Sources</p>
          <ol className="source-list">
            {res.sources.map((s) => (
              <SourceCard
                key={s.id}
                source={s}
                anchorId={anchor(s.id)}
                highlighted={highlighted === s.id}
                debug={debug}
              />
            ))}
          </ol>
        </div>
      )}
      <p className="chat-disclaimer small muted">{res.disclaimer}</p>
    </div>
  )
}
