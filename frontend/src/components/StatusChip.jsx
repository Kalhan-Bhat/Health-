import { ArrowDown, ArrowUp, Check, Minus, CircleHelp } from 'lucide-react'
import { STATUS_LABELS } from '../utils/format.js'

const ICONS = {
  low: ArrowDown,
  high: ArrowUp,
  normal: Check,
  borderline: Minus,
  unknown: CircleHelp,
}

/**
 * Status label with a colour AND a shape (arrow down / up / tick), so meaning never
 * depends on colour alone (accessibility).
 * @param {{ status: 'low'|'normal'|'high'|'borderline'|'unknown' }} props
 */
export default function StatusChip({ status }) {
  const Icon = ICONS[status]
  return (
    <span className={`status-chip status-chip--${status}`}>
      <Icon size={13} strokeWidth={2.75} aria-hidden="true" />
      <span>{STATUS_LABELS[status]}</span>
    </span>
  )
}
