/**
 * Tiny API client for the two MedBridge endpoints.
 * Every failure is normalised to { code, message } so components can show friendly text.
 */

// Empty in development: Vite proxies /api to the backend (see vite.config.js).
const BASE = import.meta.env.VITE_API_BASE_URL ?? ''

/**
 * Upload a PDF and get the AnalyzeReportResponse.
 * @param {File} file
 * @param {'simple'|'detailed'} readingLevel
 */
export async function analyzeReport(file, readingLevel = 'simple', { signal } = {}) {
  const form = new FormData()
  form.append('file', file)
  form.append('reading_level', readingLevel)
  return request('/api/analyze-report', { method: 'POST', body: form, signal })
}

/**
 * Ask the knowledge assistant a question.
 * @param {{question: string, report_context?: object, history?: Array<{role: string, content: string}>}} payload
 */
export async function askQuestion(payload, { signal } = {}) {
  return request('/api/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
}

export async function request(path, init) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, init)
  } catch (err) {
    if (err?.name === 'AbortError') throw { code: 'ABORTED', message: 'Request cancelled.' }
    throw {
      code: 'NETWORK_ERROR',
      message: 'Could not reach the MedBridge server. Is the backend running?',
    }
  }
  const body = await res.json().catch(() => null)
  if (!res.ok) throw body?.error ?? { code: 'HTTP_' + res.status, message: 'Something went wrong.' }
  return body
}
