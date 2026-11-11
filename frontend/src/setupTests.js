import '@testing-library/jest-dom/vitest'

// jsdom does not implement scrolling; the app calls it when switching views.
window.scrollTo = () => {}
