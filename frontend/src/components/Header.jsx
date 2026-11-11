import BrandMark from './BrandMark.jsx'
import { TABS } from '../utils/constants.js'

/**
 * App header with the three tabs. Uses the ARIA tabs pattern so the tabs
 * work with a keyboard (Left/Right arrows move between tabs).
 *
 * @param {{ activeTab: string, onTabChange: (id: string) => void, hasReport: boolean }} props
 */
export default function Header({ activeTab, onTabChange, hasReport, onHome }) {
  const isDisabled = (id) => id === 'dashboard' && !hasReport

  function handleKeyDown(event) {
    if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
    const enabled = TABS.filter((t) => !isDisabled(t.id))
    const index = enabled.findIndex((t) => t.id === activeTab)
    const step = event.key === 'ArrowRight' ? 1 : -1
    const next = enabled[(index + step + enabled.length) % enabled.length]
    onTabChange(next.id)
    document.getElementById(`tab-${next.id}`)?.focus()
  }

  return (
    <header className="header">
      <div className="header__inner">
        <button
          type="button"
          className="brand brand--button"
          onClick={onHome}
          aria-label="MedBridge home"
        >
          <BrandMark />
          <span>MedBridge</span>
        </button>
        <div className="tabs" role="tablist" aria-label="Sections" onKeyDown={handleKeyDown}>
          {TABS.map((tab) => {
            const disabled = isDisabled(tab.id)
            return (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                role="tab"
                type="button"
                className="tab"
                aria-selected={activeTab === tab.id}
                aria-controls={`panel-${tab.id}`}
                tabIndex={activeTab === tab.id ? 0 : -1}
                disabled={disabled}
                title={disabled ? 'Analyze a report first to see your dashboard' : undefined}
                onClick={() => onTabChange(tab.id)}
              >
                {tab.label}
              </button>
            )
          })}
        </div>
      </div>
    </header>
  )
}
