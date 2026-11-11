/**
 * Work out where to draw the reference band and the value marker (spec §11.3).
 * Pure function, exported for unit tests. Returns null when no bar can be drawn.
 *
 * The scale runs from min(low, value) − padding to max(high, value) + padding,
 * where padding = 25% of the range width. One-sided ranges ("< 200", "> 40")
 * get a band that runs to the edge of the scale.
 *
 * @returns {{ bandStart: number, bandEnd: number, marker: number } | null}  percentages 0–100
 */
export function computeBarGeometry(value, low, high) {
  if (value === null || value === undefined) return null
  if (low == null && high == null) return null

  // For one-sided ranges, use the known bound and the value to size the scale.
  const lo = low ?? Math.min(high, value) * 0.5
  const hi = high ?? Math.max(low, value) * 1.5
  const width = hi - lo || Math.abs(hi) || 1
  const padding = width * 0.25
  const scaleMin = Math.min(lo, value) - padding
  const scaleMax = Math.max(hi, value) + padding
  const toPct = (x) => ((x - scaleMin) / (scaleMax - scaleMin)) * 100

  return {
    bandStart: low == null ? 0 : toPct(low),
    bandEnd: high == null ? 100 : toPct(high),
    marker: Math.min(100, Math.max(0, toPct(value))),
  }
}
