export default function AssistSurface({
  highContrast,
  reduceMotion,
  scale,
  onHighContrast,
  onReduceMotion,
  onScale,
}: {
  highContrast: boolean
  reduceMotion: boolean
  scale: number
  onHighContrast: (v: boolean) => void
  onReduceMotion: (v: boolean) => void
  onScale: (v: number) => void
}) {
  return (
    <section className="cx2-panel" aria-labelledby="cx2-assist-title">
      <h1 id="cx2-assist-title">Assist</h1>
      <p className="lead">
        Accessibility settings for the rendered shell. Human validation with a screen reader remains pending.
      </p>
      <div className="cx2-list" role="group" aria-label="Accessibility settings">
        <label className="cx2-row">
          <span>High contrast</span>
          <input
            type="checkbox"
            checked={highContrast}
            onChange={(e) => onHighContrast(e.target.checked)}
            aria-checked={highContrast}
          />
        </label>
        <label className="cx2-row">
          <span>Reduce motion</span>
          <input
            type="checkbox"
            checked={reduceMotion}
            onChange={(e) => onReduceMotion(e.target.checked)}
            aria-checked={reduceMotion}
          />
        </label>
        <label className="cx2-row">
          <span>UI scale ({scale.toFixed(2)})</span>
          <input
            type="range"
            min={0.85}
            max={1.6}
            step={0.05}
            value={scale}
            onChange={(e) => onScale(Number(e.target.value))}
            aria-valuemin={0.85}
            aria-valuemax={1.6}
            aria-valuenow={scale}
          />
        </label>
      </div>
      <p className="lead" style={{ marginTop: 16 }}>HUMAN_A11Y_PENDING — complete the human validation packet before claiming PASS.</p>
    </section>
  )
}
