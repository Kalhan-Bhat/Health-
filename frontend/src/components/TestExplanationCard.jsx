import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import StatusChip from './StatusChip.jsx'
import { formatValue } from '../utils/format.js'

/**
 * One expandable card per test: what it measures, what the result means,
 * possible reasons (only for out-of-range results) and a note about ranges.
 * @param {{ test: object, defaultOpen?: boolean }} props
 */
export default function TestExplanationCard({ test, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  const e = test.explanation
  const bodyId = `test-body-${test.id}`
  const reasonLabel =
    test.status === 'borderline' ? 'Why it might be borderline' : 'Why it might be flagged'

  return (
    <article className={`test-card test-card--${test.status}`}>
      <button
        type="button"
        className="test-card__header"
        aria-expanded={open}
        aria-controls={bodyId}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="test-card__name">{test.name}</span>
        <span className="test-card__value">{formatValue(test)}</span>
        <StatusChip status={test.status} />
        <ChevronDown aria-hidden="true" size={18} className={open ? 'chevron rotate' : 'chevron'} />
      </button>

      {open && (
        <div id={bodyId} className="test-card__body">
          {test.reference_range_raw && (
            <p className="muted small">
              Lab reference range: {test.reference_range_raw}
              {test.unit ? ` ${test.unit}` : ''}
              {test.lab_flag ? ` · Lab flag: ${test.lab_flag}` : ''}
            </p>
          )}
          {e ? (
            <dl>
              <dt>What it measures</dt>
              <dd>{e.what_it_measures}</dd>
              <dt>What your result means</dt>
              <dd>{e.what_your_result_means}</dd>
              {e.common_reasons && (
                <>
                  <dt>{reasonLabel}</dt>
                  <dd>{e.common_reasons}</dd>
                </>
              )}
              {e.range_note && (
                <>
                  <dt>About reference ranges</dt>
                  <dd>{e.range_note}</dd>
                </>
              )}
            </dl>
          ) : (
            <p className="muted">No explanation is available for this result.</p>
          )}
        </div>
      )}
    </article>
  )
}
