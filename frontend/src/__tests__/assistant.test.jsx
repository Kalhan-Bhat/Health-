import { render, screen } from '@testing-library/react'
import ChatMessage from '../components/ChatMessage.jsx'
import { buildReportContext, linkCitations } from '../utils/chat.js'

describe('linkCitations', () => {
  it('turns markers into links', () => {
    expect(linkCitations('LDL is bad [1][2]. Yours is high [Report].')).toBe(
      'LDL is bad [1](#cite-1)[2](#cite-2). Yours is high [Report](#report).',
    )
  })
})

describe('ChatMessage', () => {
  const response = {
    answer: 'LDL is often called bad cholesterol [1]. Your LDL is high [Report].',
    grounded: true,
    sources: [
      {
        id: 1,
        title: 'LDL Cholesterol',
        section: 'What it measures',
        source_name: 'MedlinePlus',
        source_url: 'https://medlineplus.gov/ldl',
        snippet: 'LDL carries cholesterol…',
        score: 0.7,
      },
    ],
    used_report_context: true,
    follow_up_suggestions: [],
    disclaimer: 'Educational only.',
    meta: { model: 'm', retrieved: 1, processing_ms: 1 },
  }

  it('renders citation buttons, the report badge and a safe external source link', () => {
    render(<ChatMessage message={{ role: 'assistant', response }} index={0} />)
    expect(screen.getByRole('button', { name: 'Show source 1' })).toBeInTheDocument()
    expect(screen.getByText('your report')).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /MedlinePlus/ })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('shows the not-found badge for ungrounded answers', () => {
    render(
      <ChatMessage
        message={{ role: 'assistant', response: { ...response, grounded: false, sources: [] } }}
        index={0}
      />,
    )
    expect(screen.getByText(/Not found in knowledge base/)).toBeInTheDocument()
  })
})

it('buildReportContext sends only the slim fields', () => {
  const ctx = buildReportContext({
    report_id: 'r1',
    report_type: 'Lipid Profile',
    tests: [
      {
        id: 't1',
        name: 'LDL',
        value: 162,
        unit: 'mg/dL',
        reference_range_raw: '< 100',
        status: 'high',
        explanation: { what_it_measures: 'x' },
      },
    ],
  })
  expect(ctx.tests[0]).toEqual({
    name: 'LDL',
    value: 162,
    unit: 'mg/dL',
    reference_range_raw: '< 100',
    status: 'high',
  })
})
