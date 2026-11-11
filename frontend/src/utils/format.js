/** Small formatting helpers shared by several components. */

/** Order used when listing results: out-of-range first. */
export const STATUS_ORDER = { high: 0, low: 1, borderline: 2, unknown: 3, normal: 4 }

export const STATUS_LABELS = {
  low: 'Low',
  normal: 'Normal',
  high: 'High',
  borderline: 'Borderline',
  unknown: 'Unknown',
}

/** Words used in screen-reader labels ("below reference range"). */
export const STATUS_PHRASES = {
  low: 'below reference range',
  high: 'above reference range',
  normal: 'within reference range',
  borderline: 'marked borderline by the lab',
  unknown: 'status unknown',
}

/** Format a number without long decimals, keeping thousands readable (245000 → "245,000"). */
export function formatNumber(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return ''
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 })
}

/** "10.8 g/dL" — uses the raw printed value so it matches the report exactly. */
export function formatValue(test) {
  return [test.value_raw, test.unit].filter(Boolean).join(' ')
}

export function isAbnormal(test) {
  return test.status === 'low' || test.status === 'high' || test.status === 'borderline'
}

/** Sort a copy of the tests so out-of-range results come first, report order otherwise. */
export function sortByConcern(tests) {
  return tests
    .map((t, i) => ({ t, i }))
    .sort((a, b) => STATUS_ORDER[a.t.status] - STATUS_ORDER[b.t.status] || a.i - b.i)
    .map(({ t }) => t)
}

export function formatBytes(bytes) {
  return bytes < 1024 * 1024
    ? `${Math.round(bytes / 1024)} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
