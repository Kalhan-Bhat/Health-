import { computeBarGeometry } from '../utils/rangeGeometry.js'
import { formatNumber } from '../utils/format.js'

/**
 * The visual core of MedBridge: a track, the lab's reference band, tick marks
 * labelled with the lab's limits, and a marker for the person's value.
 * Plain divs positioned by percentage — no chart library.
 *
 * @param {{ value: number, low: number|null, high: number|null, status: string,
 *           label: string, size?: 'regular'|'hero', valueText?: string }} props
 */
export default function RangeGauge({
  value,
  low,
  high,
  status,
  label,
  size = 'regular',
  valueText,
}) {
  const g = computeBarGeometry(value, low, high)
  if (!g) return null

  return (
    <div className={`gauge gauge--${size}`} role="img" aria-label={label}>
      <div className="gauge__track">
        <div
          className="gauge__band"
          style={{
            left: `${g.bandStart}%`,
            width: `${Math.max(g.bandEnd - g.bandStart, 0)}%`,
          }}
        />
        <div
          className={`gauge__marker gauge__marker--${status}`}
          style={{ '--from': `${(g.bandStart + g.bandEnd) / 2}%`, left: `${g.marker}%` }}
        >
          {valueText && <span className="gauge__value">{valueText}</span>}
        </div>
      </div>
      <div className="gauge__ticks" aria-hidden="true">
        {low != null && (
          <span className="gauge__tick" style={{ left: `${g.bandStart}%` }}>
            {formatNumber(low)}
          </span>
        )}
        {high != null && (
          <span className="gauge__tick" style={{ left: `${g.bandEnd}%` }}>
            {formatNumber(high)}
          </span>
        )}
      </div>
    </div>
  )
}
