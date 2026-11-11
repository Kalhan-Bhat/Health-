import { ExternalLink } from 'lucide-react'

/**
 * One knowledge-base source under an assistant answer.
 * The similarity score is shown only in debug mode (add ?debug to the URL).
 *
 * @param {{ source: object, anchorId: string, highlighted?: boolean, debug?: boolean }} props
 */
export default function SourceCard({ source, anchorId, highlighted = false, debug = false }) {
  return (
    <li id={anchorId} className={`source-card ${highlighted ? 'source-card--highlight' : ''}`}>
      <span className="source-card__num" aria-hidden="true">
        {source.id}
      </span>
      <div className="source-card__body">
        <p className="source-card__title">
          {source.title}
          {source.section && <span className="source-card__section">{source.section}</span>}
        </p>
        <p className="source-card__snippet small">{source.snippet}</p>
        <p className="small source-card__meta">
          {source.source_url ? (
            <a href={source.source_url} target="_blank" rel="noopener noreferrer">
              {source.source_name} <ExternalLink size={13} aria-hidden="true" />
              <span className="visually-hidden"> (opens in a new tab)</span>
            </a>
          ) : (
            source.source_name
          )}
          {debug && <span className="muted"> (similarity {source.score.toFixed(3)})</span>}
        </p>
      </div>
    </li>
  )
}
