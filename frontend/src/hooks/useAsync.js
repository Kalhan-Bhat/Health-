import { useCallback, useRef, useState } from 'react'

/**
 * Runs an async function and tracks { loading, error, data }.
 * Starting a new run cancels the previous one (via AbortController).
 *
 * @template T
 * @param {(...args: any[]) => Promise<T>} fn  receives the args plus { signal } last
 */
export default function useAsync(fn) {
  const [state, setState] = useState({ loading: false, error: null, data: null })
  const controllerRef = useRef(null)

  const run = useCallback(
    async (...args) => {
      controllerRef.current?.abort()
      const controller = new AbortController()
      controllerRef.current = controller
      setState({ loading: true, error: null, data: null })
      try {
        const data = await fn(...args, { signal: controller.signal })
        setState({ loading: false, error: null, data })
        return data
      } catch (error) {
        if (error?.code === 'ABORTED') return null
        setState({ loading: false, error, data: null })
        return null
      }
    },
    [fn],
  )

  const reset = useCallback(() => {
    controllerRef.current?.abort()
    setState({ loading: false, error: null, data: null })
  }, [])

  return { ...state, run, reset }
}
