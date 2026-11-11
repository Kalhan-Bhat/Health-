import StatusChip from './StatusChip.jsx'

/**
 * Overview card: report type, patient context, plain-language overview,
 * key findings and the status counts.
 * @param {{ report: object }} props
 */
export default function ReportSummary({ report }) {
  const { summary, patient_context: pc, report_type: reportType } = report
  const details = [
    pc.age && `Age ${pc.age}`,
    pc.sex,
    pc.report_date && `Date ${pc.report_date}`,
    pc.lab_name,
  ].filter(Boolean)
  const counts = summary.counts

  return (
    <section className="card summary print-keep" aria-labelledby="summary-title">
      <p className="eyebrow">Your report</p>
      <h1 id="summary-title">{reportType}</h1>
      {details.length > 0 && <p className="muted small">{details.join(' · ')}</p>}

      <div className="count-row" aria-label="Result counts">
        <span className="count-pill">
          <strong>{counts.total}</strong> results
        </span>
        {['normal', 'low', 'high', 'borderline', 'unknown'].map((s) =>
          counts[s] > 0 ? (
            <span key={s} className="count-pill">
              <strong>{counts[s]}</strong> <StatusChip status={s} />
            </span>
          ) : null,
        )}
      </div>

      <h2>Overview</h2>
      <p>{summary.overview}</p>

      {summary.key_findings.length > 0 && (
        <>
          <h2>Key findings</h2>
          <ul className="findings">
            {summary.key_findings.map((k, i) => (
              <li key={i}>{k}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
