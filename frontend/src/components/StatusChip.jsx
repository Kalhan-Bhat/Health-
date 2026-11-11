import { STATUS_LABELS } from '../utils/format.js'

/**
 * Text status label with a colour. The text is always shown, so meaning never
 * depends on colour alone (accessibility).
 * @param {{ status: 'low'|'normal'|'high'|'borderline'|'unknown' }} props
 */
export default function StatusChip({ status }) {
  return <span className={`status-chip status-chip--${status}`}>{STATUS_LABELS[status]}</span>
}
