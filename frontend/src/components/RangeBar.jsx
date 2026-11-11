import StatusChip from './StatusChip.jsx'
import { STATUS_PHRASES, formatNumber, formatValue } from '../utils/format.js'
import { computeBarGeometry } from '../utils/rangeGeometry.js'

/** Human-readable range text, e.g. "12 – 15.5 g/dL", "below 200 mg/dL", "above 40 mg/dL". */
function rangeText(test) {
  const unit = test.unit ? ` ${test.unit}` : ''
  if (test.ref_low != null && test.ref_high != null)
    return `${formatNumber(test.ref_low)} – ${formatNumber(test.ref_high)}${unit}`
  if (test.ref_high != null) return `up to ${formatNumber(test.ref_high)}${unit}`
  if (test.ref_low != null) return `${formatNumber(test.ref_low)} or more${unit}`
  return test.reference_range_raw ?? 'not given'
}

/**
 * One dashboard row: test name, value, status chip and the range bar.
 * Plain divs positioned by percentage — no chart library needed.
 * @param {{ test: object }} props
 */
export default function RangeBar({ test }) {
  const geometry = computeBarGeometry(test.value, test.ref_low, test.ref_high)
  const label = `${test.name} ${formatValue(test)}, ${STATUS_PHRASES[test.status]}${
    geometry ? ` ${rangeText(test).replace('–', 'to')}` : ''
  }`

  return (
    <div className="range-row">
      <div className="range-row__top">
        <span className="range-row__name">{test.name}</span>
        <span className="range-row__value">{formatValue(test)}</span>
        <StatusChip status={test.status} />
      </div>

      {geometry ? (
        <>
          <div className="range-bar" role="img" aria-label={label}>
            <div
              className="range-bar__band"
              style={{
                left: `${geometry.bandStart}%`,
                width: `${Math.max(geometry.bandEnd - geometry.bandStart, 0)}%`,
              }}
            />
            <div
              className={`range-bar__marker range-bar__marker--${test.status}`}
              style={{ left: `${geometry.marker}%` }}
            />
          </div>
          <p className="range-row__caption small muted">Lab reference range: {rangeText(test)}</p>
        </>
      ) : (
        <p className="range-row__caption small muted" aria-label={label}>
          {test.reference_range_raw
            ? `Lab reference: ${test.reference_range_raw}. `
            : 'No reference range given. '}
          Range couldn&apos;t be displayed — see your report.
        </p>
      )}
    </div>
  )
}
