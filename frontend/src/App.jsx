import { useCallback, useRef, useState } from 'react'
import { RotateCcw } from 'lucide-react'
import Header from './components/Header.jsx'
import DisclaimerBanner from './components/DisclaimerBanner.jsx'
import UploadPanel from './components/UploadPanel.jsx'
import LoadingState from './components/LoadingState.jsx'
import ErrorState from './components/ErrorState.jsx'
import ReportSummary from './components/ReportSummary.jsx'
import RedFlagAlert from './components/RedFlagAlert.jsx'
import TestExplanationCard from './components/TestExplanationCard.jsx'
import DoctorQuestions from './components/DoctorQuestions.jsx'
import HealthDashboard from './components/HealthDashboard.jsx'
import { analyzeReport } from './api/client.js'
import useAsync from './hooks/useAsync.js'
import { ANALYZE_STAGES, SAMPLE_REPORTS } from './utils/constants.js'
import { isAbnormal, sortByConcern } from './utils/format.js'

/**
 * Root component. Holds the global state:
 *  - report:    the AnalyzeReportResponse (kept in memory only — never in localStorage, for privacy)
 *  - activeTab: which tab is visible
 */
export default function App() {
  const [activeTab, setActiveTab] = useState('report')
  const [report, setReport] = useState(null)
  const analyze = useAsync(analyzeReport)
  // Remember the last upload so "Try again" can resend it without re-picking the file.
  const lastRequest = useRef(null)

  const handleAnalyze = useCallback(
    async (file, readingLevel) => {
      lastRequest.current = { file, readingLevel }
      const result = await analyze.run(file, readingLevel)
      if (result) setReport(result)
    },
    [analyze],
  )

  function retry() {
    if (lastRequest.current)
      handleAnalyze(lastRequest.current.file, lastRequest.current.readingLevel)
  }

  function startOver() {
    analyze.reset()
    setReport(null)
    lastRequest.current = null
    setActiveTab('report')
  }

  return (
    <div className="app">
      <Header activeTab={activeTab} onTabChange={setActiveTab} hasReport={report !== null} />
      <DisclaimerBanner />
      <main className="main">
        <section
          id="panel-report"
          role="tabpanel"
          aria-labelledby="tab-report"
          hidden={activeTab !== 'report'}
        >
          {report ? (
            <ReportView report={report} onStartOver={startOver} />
          ) : analyze.loading ? (
            <div className="card">
              <LoadingState messages={ANALYZE_STAGES} />
            </div>
          ) : (
            <>
              {analyze.error && (
                <ErrorState error={analyze.error} onRetry={retry}>
                  {analyze.error.code === 'SCANNED_PDF_UNSUPPORTED' && (
                    <p className="small">
                      Tip: try one of the sample reports below, such as the{' '}
                      {SAMPLE_REPORTS[0].label.toLowerCase()} sample.
                    </p>
                  )}
                </ErrorState>
              )}
              <UploadPanel onAnalyze={handleAnalyze} disabled={analyze.loading} />
            </>
          )}
        </section>

        <section
          id="panel-dashboard"
          role="tabpanel"
          aria-labelledby="tab-dashboard"
          hidden={activeTab !== 'dashboard'}
        >
          {report && <HealthDashboard report={report} />}
        </section>

        <section
          id="panel-ask"
          role="tabpanel"
          aria-labelledby="tab-ask"
          hidden={activeTab !== 'ask'}
        >
          <div className="card">Knowledge assistant is coming in a later phase.</div>
        </section>
      </main>
    </div>
  )
}

/** Everything shown on the Report tab once a report has been analysed. */
function ReportView({ report, onStartOver }) {
  const tests = sortByConcern(report.tests)
  return (
    <div className="stack">
      <RedFlagAlert flags={report.red_flags} />
      <ReportSummary report={report} />

      <section className="card no-print" aria-labelledby="tests-title">
        <h2 id="tests-title">Your results explained</h2>
        <p className="muted small">
          Results outside the lab&apos;s range are listed first. Tap a result to read more.
        </p>
        <div className="test-list">
          {tests.map((t) => (
            <TestExplanationCard key={t.id} test={t} defaultOpen={isAbnormal(t)} />
          ))}
        </div>
        {report.unparsed_lines.length > 0 && (
          <details className="unparsed">
            <summary>
              Some results couldn&apos;t be read automatically ({report.unparsed_lines.length})
            </summary>
            <ul>
              {report.unparsed_lines.map((line, i) => (
                <li key={i}>{line}</li>
              ))}
            </ul>
          </details>
        )}
      </section>

      <DoctorQuestions questions={report.doctor_questions} />

      <p className="disclaimer-footer small print-keep">{report.disclaimer}</p>

      <div className="no-print">
        <button type="button" className="btn btn--secondary" onClick={onStartOver}>
          <RotateCcw size={16} aria-hidden="true" /> Analyze another report
        </button>
      </div>
    </div>
  )
}
