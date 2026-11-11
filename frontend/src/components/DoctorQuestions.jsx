import { useState } from 'react'
import { Copy, Printer, Check } from 'lucide-react'

/**
 * Checklist of questions to take to the doctor, with "Copy all" and "Print".
 * The print stylesheet prints only the summary, these questions and the disclaimer.
 * @param {{ questions: string[] }} props
 */
export default function DoctorQuestions({ questions }) {
  const [checked, setChecked] = useState(() => questions.map(() => false))
  const [copied, setCopied] = useState(false)

  async function copyAll() {
    const text = questions.map((q, i) => `${i + 1}. ${q}`).join('\n')
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  return (
    <section className="card doctor-questions print-keep" aria-labelledby="dq-title">
      <div className="section-header">
        <h2 id="dq-title">Questions to ask your doctor</h2>
        <div className="button-row no-print">
          <button type="button" className="btn btn--secondary" onClick={copyAll}>
            {copied ? (
              <Check size={16} aria-hidden="true" />
            ) : (
              <Copy size={16} aria-hidden="true" />
            )}
            {copied ? 'Copied' : 'Copy all'}
          </button>
          <button type="button" className="btn btn--secondary" onClick={() => window.print()}>
            <Printer size={16} aria-hidden="true" /> Print
          </button>
        </div>
      </div>
      <ul className="checklist">
        {questions.map((q, i) => (
          <li key={i}>
            <label>
              <input
                type="checkbox"
                checked={checked[i] ?? false}
                onChange={() => setChecked((c) => c.map((v, j) => (j === i ? !v : v)))}
              />
              <span>{q}</span>
            </label>
          </li>
        ))}
      </ul>
      <span className="visually-hidden" aria-live="polite">
        {copied ? 'Questions copied to clipboard' : ''}
      </span>
    </section>
  )
}
