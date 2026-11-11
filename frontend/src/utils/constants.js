/** Shared limits and static text. Upload limits mirror the backend (.env.example). */

export const MAX_UPLOAD_MB = 10
export const MAX_QUESTION_CHARS = 500
export const MAX_HISTORY_TURNS = 6

/** Tab ids used by App and Header. */
export const TABS = [
  { id: 'report', label: 'Report' },
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'ask', label: 'Ask' },
]

export const SHORT_DISCLAIMER = 'Educational information only — not medical advice.'
