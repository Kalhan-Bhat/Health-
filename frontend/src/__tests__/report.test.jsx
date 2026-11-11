import { render, screen } from '@testing-library/react'
import { computeBarGeometry } from '../utils/rangeGeometry.js'
import RangeBar from '../components/RangeBar.jsx'
import App from '../App.jsx'

describe('computeBarGeometry', () => {
  it('places a low value left of the band', () => {
    const g = computeBarGeometry(10.8, 12, 15.5)
    expect(g.marker).toBeLessThan(g.bandStart)
    expect(g.bandEnd).toBeGreaterThan(g.bandStart)
  })

  it('places a normal value inside the band', () => {
    const g = computeBarGeometry(13, 12, 15.5)
    expect(g.marker).toBeGreaterThan(g.bandStart)
    expect(g.marker).toBeLessThan(g.bandEnd)
  })

  it('places a high value right of the band', () => {
    const g = computeBarGeometry(16.5, 12, 15.5)
    expect(g.marker).toBeGreaterThan(g.bandEnd)
  })

  it('handles one-sided ranges', () => {
    const upper = computeBarGeometry(162, null, 100) // "< 100"
    expect(upper.bandStart).toBe(0)
    expect(upper.marker).toBeGreaterThan(upper.bandEnd)
    const lower = computeBarGeometry(38, 40, null) // "> 40"
    expect(lower.bandEnd).toBe(100)
    expect(lower.marker).toBeLessThan(lower.bandStart)
  })

  it('returns null when there is nothing to draw', () => {
    expect(computeBarGeometry(null, 12, 15)).toBeNull()
    expect(computeBarGeometry(5, null, null)).toBeNull()
  })
})

describe('RangeBar', () => {
  const base = { id: 't1', name: 'Haemoglobin', value_raw: '10.8', unit: 'g/dL' }

  it('renders a bar with an accessible label', () => {
    render(<RangeBar test={{ ...base, value: 10.8, ref_low: 12, ref_high: 15.5, status: 'low' }} />)
    expect(screen.getByRole('img').getAttribute('aria-label')).toMatch(/below reference range/)
    expect(screen.getByText('Low')).toBeInTheDocument()
  })

  it('renders no bar when the range is missing', () => {
    render(
      <RangeBar
        test={{ ...base, value: null, ref_low: null, ref_high: null, status: 'unknown' }}
      />,
    )
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.getByText(/couldn.t be displayed/)).toBeInTheDocument()
  })
})

describe('App', () => {
  it('renders the shell with the Dashboard tab disabled before a report', () => {
    render(<App />)
    expect(screen.getByRole('tab', { name: 'Report' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('tab', { name: 'Dashboard' })).toBeDisabled()
    expect(screen.getByText('Explain my report')).toBeDisabled() // consent not ticked yet
  })
})
