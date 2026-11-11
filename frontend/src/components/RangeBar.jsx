import StatusChip from './StatusChip.jsx'
import RangeGauge from './RangeGauge.jsx'
import { STATUS_PHRASES, formatNumber, formatValue } from '../utils/format.js'
import { computeBarGeometry } from '../utils/rangeGeometry.js'

/** Human-readable range text, e.g. "12 – 15.5 g/dL", "up to 200 mg/dL", "40 or more mg/dL". */
function rangeText(test) {
  const unit = test.unit ? ` ${test.unit}` : ''
  if (test.ref_low != null && test.ref_high != null)
    return `${formatNumber(test.ref_low)} – ${formatNumber(test.ref_high)}${unit}`
  if (test.ref_high != null) return `up to ${formatNumber(test.ref_high)}${unit}`
  if (test.ref_low != null) return `${formatNumber(test.ref_low)} or more${unit}`
  return test.reference_range_raw ?? 'not given'
}

/**
 * One dashboard row: test name, value, status chip and the range gauge.
 * @param {{ test: object }} props
 */
export default function RangeBar({ test }) {
  const drawable = computeBarGeometry(test.value, test.ref_low, test.ref_high) !== null
  const label = `${test.name} ${formatValue(test)}, ${STATUS_PHRASES[test.status]}${
    drawable ? ` ${rangeText(test).replace('–', 'to')}` : ''
  }`

  return (
    <div className={`range-row range-row--${test.status}`}>
      <div className="range-row__top">
        <span className="range-row__name">{test.name}</span>
        <span className="range-row__value">{formatValue(test)}</span>
        <StatusChip status={test.status} />
      </div>

      {drawable ? (
        <>
          <RangeGauge
            value={test.value}
            low={test.ref_low}
            high={test.ref_high}
            status={test.status}
            label={label}
          />
          <p className="range-row__caption">Lab reference range: {rangeText(test)}</p>
        </>
      ) : (
        <p className="range-row__caption range-row__caption--none" aria-label={label}>
          {test.reference_range_raw
            ? `Lab reference: ${test.reference_range_raw}. `
            : 'No reference range given. '}
          Range couldn&apos;t be displayed — see your report.
        </p>
      )}
    </div>
  )
}
