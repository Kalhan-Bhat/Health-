import { AlertCircle } from 'lucide-react'
import { ERROR_MESSAGES, RETRYABLE_ERRORS } from '../utils/constants.js'

/**
 * Friendly error box. Maps the backend error `code` to plain-language copy.
 * @param {{ error: {code: string, message?: string}, onRetry?: () => void, children?: any }} props
 */
export default function ErrorState({ error, onRetry, children }) {
  const message = ERROR_MESSAGES[error?.code] ?? error?.message ?? 'Something went wrong.'
  return (
    <div className="error-state" role="alert">
      <AlertCircle aria-hidden="true" size={20} />
      <div>
        <p className="error-state__message">{message}</p>
        {children}
        {onRetry && RETRYABLE_ERRORS.has(error?.code) && (
          <button type="button" className="btn btn--secondary" onClick={onRetry}>
            Try again
          </button>
        )}
      </div>
    </div>
  )
}
