import { STATUS_LABELS } from '../utils/format.js'

const ORDER = ['normal', 'borderline', 'low', 'high', 'unknown']

/**
 * The top of the report: report type, the lab's details, a single proportion bar
 * showing how the results split by status, the plain-language overview and key findings.
 * @param {{ report: object }} props
 */
export default function ReportSummary({ report }) {
  const { summary, patient_context: pc, report_type: reportType } = report
  const counts = summary.counts
  const details = [
    ['Lab', pc.lab_name],
    ['Date', pc.report_date],
    ['Age', pc.age],
    ['Sex', pc.sex],
  ].filter(([, v]) => v)
  const segments = ORDER.filter((s) => counts[s] > 0)
  const outside = counts.low + counts.high + counts.borderline

  return (
    <section className="summary print-keep" aria-labelledby="summary-title">
      <h1 id="summary-title" className="summary__title">
        {reportType}
      </h1>
      {details.length > 0 && (
        <dl className="summary__details">
          {details.map(([k, v]) => (
            <div key={k}>
              <dt>{k}</dt>
              <dd>{v}</dd>
            </div>
          ))}
        </dl>
      )}

      <div className="proportion">
        <p className="proportion__lede">
          {outside === 0
            ? `All ${counts.total} results are inside the lab's ranges.`
            : `${outside} of ${counts.total} results sit outside the lab's ranges.`}
        </p>
        <div className="proportion__bar" aria-hidden="true">
          {segments.map((s) => (
            <span
              key={s}
              className={`proportion__seg proportion__seg--${s}`}
              style={{ flexGrow: counts[s] }}
            />
          ))}
        </div>
        <ul className="proportion__legend" aria-label="Result counts">
          {segments.map((s) => (
            <li key={s}>
              <span className={`dot dot--${s}`} aria-hidden="true" />
              <strong>{counts[s]}</strong> {STATUS_LABELS[s].toLowerCase()}
            </li>
          ))}
        </ul>
      </div>

      <div className="summary__body">
        <p className="summary__overview">{summary.overview}</p>
        {summary.key_findings.length > 0 && (
          <>
            <h2>What stands out</h2>
            <ul className="findings">
              {summary.key_findings.map((k, i) => (
                <li key={i}>{k}</li>
              ))}
            </ul>
          </>
        )}
      </div>
    </section>
  )
}
