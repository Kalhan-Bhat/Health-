/**
 * The MedBridge mark: a tiny reference-range bar with a marker resting inside the band.
 * It echoes the dashboard gauges, so the logo explains the product.
 */
export default function BrandMark({ size = 28 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      aria-hidden="true"
      focusable="false"
      className="brand-mark"
    >
      <rect width="32" height="32" rx="9" fill="var(--petrol)" />
      <rect x="6" y="15" width="20" height="3" rx="1.5" fill="#ffffff" opacity="0.35" />
      <rect x="11" y="15" width="10" height="3" rx="1.5" fill="var(--sage)" />
      <circle cx="17" cy="16.5" r="4" fill="#ffffff" stroke="var(--petrol)" strokeWidth="2" />
    </svg>
  )
}
