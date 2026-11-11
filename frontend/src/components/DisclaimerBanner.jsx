import { useState } from 'react'
import { Info, ChevronDown, ChevronUp } from 'lucide-react'
import { SHORT_DISCLAIMER } from '../utils/constants.js'

const FULL_DISCLAIMER =
  'MedBridge provides educational information only and is not a substitute for professional ' +
  'medical advice, diagnosis, or treatment. Always discuss your results with a qualified ' +
  'healthcare provider. If you think you may have a medical emergency, contact your local ' +
  'emergency number immediately. Report text is sent to an AI service (Groq) to generate ' +
  'explanations; it is not stored by MedBridge.'

/** Persistent, collapsible disclaimer shown under the header on every tab. */
export default function DisclaimerBanner() {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="disclaimer-banner" role="note">
      <div className="disclaimer-banner__inner">
        <Info aria-hidden="true" size={18} />
        <p>{expanded ? FULL_DISCLAIMER : SHORT_DISCLAIMER}</p>
        <button
          type="button"
          className="icon-button"
          aria-expanded={expanded}
          aria-label={expanded ? 'Show less' : 'Read the full disclaimer'}
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>
    </div>
  )
}
