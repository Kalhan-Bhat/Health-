/** Helpers for the Ask tab (kept out of component files so Fast Refresh works). */

/**
 * Turn citation markers into markdown links that we render as small buttons:
 *   "[1]"      → "[1](#cite-1)"
 *   "[Report]" → "[Report](#report)"
 * Markers that are already links are left alone.
 */
export function linkCitations(text) {
  return text
    .replace(/\[(\d+)\](?!\()/g, '[$1](#cite-$1)')
    .replace(/\[Report\](?!\()/g, '[Report](#report)')
}

/** Build the slim report context the backend expects (spec §7.2). */
export function buildReportContext(report) {
  return {
    report_id: report.report_id,
    report_type: report.report_type,
    tests: report.tests.slice(0, 60).map((t) => ({
      name: t.name,
      value: t.value,
      unit: t.unit,
      reference_range_raw: t.reference_range_raw,
      status: t.status,
    })),
  }
}
