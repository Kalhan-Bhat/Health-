import { useState } from 'react'
import Header from './components/Header.jsx'
import DisclaimerBanner from './components/DisclaimerBanner.jsx'

/**
 * Root component. Holds the global state:
 *  - report:   the AnalyzeReportResponse (kept in memory only — never in localStorage, for privacy)
 *  - activeTab: which tab is visible
 */
export default function App() {
  const [activeTab, setActiveTab] = useState('report')
  const [report] = useState(null)

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
          <div className="card">
            <h1>Understand your lab report</h1>
            <p>Report upload is coming in the next phase.</p>
          </div>
        </section>
        <section
          id="panel-dashboard"
          role="tabpanel"
          aria-labelledby="tab-dashboard"
          hidden={activeTab !== 'dashboard'}
        >
          <div className="card">Dashboard</div>
        </section>
        <section id="panel-ask" role="tabpanel" aria-labelledby="tab-ask" hidden={activeTab !== 'ask'}>
          <div className="card">Knowledge assistant is coming in a later phase.</div>
        </section>
      </main>
    </div>
  )
}
