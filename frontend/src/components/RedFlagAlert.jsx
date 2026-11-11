import { AlertTriangle } from 'lucide-react'

/**
 * Shown when the LAB itself marked a value as critical. MedBridge never invents
 * its own critical thresholds; it only passes on the lab's marker.
 * @param {{ flags: Array<{test_id?: string, message: string}> }} props
 */
export default function RedFlagAlert({ flags }) {
  if (!flags?.length) return null
  return (
    <div className="red-flag" role="alert">
      <AlertTriangle aria-hidden="true" size={22} />
      <div>
        <h2 className="red-flag__title">Your lab marked a result as critical</h2>
        <ul>
          {flags.map((f, i) => (
            <li key={f.test_id ?? i}>{f.message}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
