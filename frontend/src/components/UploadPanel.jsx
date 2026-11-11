import { useRef, useState } from 'react'
import { FileUp, FileText, ShieldCheck } from 'lucide-react'
import { MAX_UPLOAD_MB, SAMPLE_REPORTS } from '../utils/constants.js'
import { formatBytes } from '../utils/format.js'
import RangeGauge from './RangeGauge.jsx'

/**
 * Drag-and-drop PDF upload with client-side checks, reading level toggle,
 * a required consent checkbox, and "Try a sample report" buttons.
 *
 * @param {{ onAnalyze: (file: File, readingLevel: string) => void, disabled?: boolean }} props
 */
export default function UploadPanel({ onAnalyze, disabled = false }) {
  const [file, setFile] = useState(null)
  const [readingLevel, setReadingLevel] = useState('simple')
  const [consent, setConsent] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [localError, setLocalError] = useState('')
  const inputRef = useRef(null)

  /** Mirror the backend checks so obvious mistakes are caught instantly. */
  function pickFile(candidate) {
    setLocalError('')
    if (!candidate) return
    const isPdf =
      candidate.name.toLowerCase().endsWith('.pdf') &&
      (candidate.type === 'application/pdf' || candidate.type === '')
    if (!isPdf) {
      setFile(null)
      setLocalError('Only PDF files are supported. Please choose a .pdf file.')
      return
    }
    if (candidate.size > MAX_UPLOAD_MB * 1024 * 1024) {
      setFile(null)
      setLocalError(`This file is larger than ${MAX_UPLOAD_MB} MB. Please choose a smaller PDF.`)
      return
    }
    setFile(candidate)
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragOver(false)
    pickFile(event.dataTransfer.files?.[0])
  }

  async function loadSample(sample) {
    setLocalError('')
    try {
      const res = await fetch(`/samples/${sample.file}`)
      if (!res.ok) throw new Error('missing sample')
      const blob = await res.blob()
      const sampleFile = new File([blob], sample.file, { type: 'application/pdf' })
      setFile(sampleFile)
      onAnalyze(sampleFile, readingLevel)
    } catch {
      setLocalError('The sample report could not be loaded.')
    }
  }

  const canSubmit = file && consent && !disabled

  return (
    <>
      <section className="hero" aria-labelledby="upload-title">
        <div className="hero__text">
          <h1 id="upload-title" className="hero__title">
            See where your numbers sit.
          </h1>
          <p className="hero__lede">
            Upload a lab report. MedBridge explains each result in plain words, shows it against
            your lab&apos;s own range, and suggests questions for your doctor.
          </p>
        </div>
        <figure className="specimen" aria-label="Example result">
          <div className="specimen__head">
            <span className="specimen__name">Haemoglobin</span>
            <span className="specimen__unit">g/dL</span>
          </div>
          <RangeGauge
            size="hero"
            value={10.8}
            low={12}
            high={15.5}
            status="low"
            valueText="10.8"
            label="Example: haemoglobin 10.8 g/dL, below the lab's range of 12.0 to 15.5"
          />
          <figcaption>
            The green band is the lab&apos;s range. This example result is just below it.
          </figcaption>
        </figure>
      </section>

      <section className="card upload" aria-label="Upload your report">
        <div
          className={`dropzone ${dragOver ? 'dropzone--active' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragOver(true)
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <FileUp aria-hidden="true" size={30} strokeWidth={1.75} />
          {file ? (
            <p className="dropzone__file">
              <FileText aria-hidden="true" size={18} /> {file.name}{' '}
              <span className="muted small">({formatBytes(file.size)})</span>
            </p>
          ) : (
            <p>Drag and drop your PDF here</p>
          )}
          <button
            type="button"
            className="btn btn--secondary"
            onClick={() => inputRef.current?.click()}
            disabled={disabled}
          >
            Choose PDF
          </button>
          <label htmlFor="pdf-input" className="visually-hidden">
            Choose a PDF lab report
          </label>
          <input
            id="pdf-input"
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            hidden
            onChange={(e) => pickFile(e.target.files?.[0])}
          />
          <p className="muted small">
            Digital (text-based) PDF, up to {MAX_UPLOAD_MB} MB and 20 pages
          </p>
        </div>

        {localError && (
          <p className="field-error" role="alert">
            {localError}
          </p>
        )}

        <fieldset className="reading-level">
          <legend>Explanation style</legend>
          <label>
            <input
              type="radio"
              name="reading-level"
              value="simple"
              checked={readingLevel === 'simple'}
              onChange={() => setReadingLevel('simple')}
            />
            Simple
          </label>
          <label>
            <input
              type="radio"
              name="reading-level"
              value="detailed"
              checked={readingLevel === 'detailed'}
              onChange={() => setReadingLevel('detailed')}
            />
            Detailed
          </label>
        </fieldset>

        <label className="consent">
          <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
          <span>I understand MedBridge is for education and does not replace my doctor.</span>
        </label>

        <button
          type="button"
          className="btn btn--primary btn--wide"
          disabled={!canSubmit}
          onClick={() => onAnalyze(file, readingLevel)}
        >
          Explain my report
        </button>

        <p className="privacy-note small">
          <ShieldCheck aria-hidden="true" size={16} />
          Your file is processed for this session only and is not stored. Report text is sent to an
          AI service (Groq) to generate explanations.
        </p>

        <div className="samples">
          <p className="small">
            <strong>No report handy?</strong> Try a synthetic sample report
            {!consent && ' (tick the box above first)'}:
          </p>
          <div className="button-row">
            {SAMPLE_REPORTS.map((s) => (
              <button
                key={s.file}
                type="button"
                className="btn btn--secondary btn--small"
                disabled={!consent || disabled}
                onClick={() => loadSample(s)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
