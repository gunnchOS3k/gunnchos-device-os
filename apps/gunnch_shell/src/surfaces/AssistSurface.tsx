import Icon from '../design/icons/Icon'
import { SurfaceHeader } from '../design/primitives/SurfaceChrome'

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
    <section className="cx2-panel vxp-assist" aria-labelledby="cx2-assist-title">
      <SurfaceHeader
        titleId="cx2-assist-title"
        title="Assist"
        lead="Accessibility controls for the rendered shell. Labels stay visible; focus rings stay strong."
      />

      <div className="vxp-assist-list" role="group" aria-label="Accessibility settings">
        <label className="vxp-assist-row" htmlFor="assist-hc">
          <span className="vxp-assist-copy">
            <Icon name="assist" size={20} />
            <span>
              <strong>High contrast</strong>
              <em>Stronger edges and ink for low-vision reading</em>
            </span>
          </span>
          <input
            id="assist-hc"
            type="checkbox"
            checked={highContrast}
            onChange={(e) => onHighContrast(e.target.checked)}
            aria-checked={highContrast}
          />
        </label>
        <label className="vxp-assist-row" htmlFor="assist-rm">
          <span className="vxp-assist-copy">
            <Icon name="status_warn" size={20} />
            <span>
              <strong>Reduce motion</strong>
              <em>Disable non-essential transitions and animation</em>
            </span>
          </span>
          <input
            id="assist-rm"
            type="checkbox"
            checked={reduceMotion}
            onChange={(e) => onReduceMotion(e.target.checked)}
            aria-checked={reduceMotion}
          />
        </label>
        <label className="vxp-assist-row" htmlFor="assist-scale">
          <span className="vxp-assist-copy">
            <Icon name="search" size={20} />
            <span>
              <strong>UI scale ({scale.toFixed(2)})</strong>
              <em>Grow touch targets and type without layout collapse</em>
            </span>
          </span>
          <input
            id="assist-scale"
            type="range"
            min={0.85}
            max={1.6}
            step={0.05}
            value={scale}
            onChange={(e) => onScale(Number(e.target.value))}
            aria-valuemin={0.85}
            aria-valuemax={1.6}
            aria-valuenow={scale}
            aria-label={`UI scale ${scale.toFixed(2)}`}
          />
        </label>
      </div>

      <p className="lead" role="note">
        HUMAN_A11Y_PENDING — complete the human validation packet before claiming PASS. This surface does not claim WCAG
        certification.
      </p>
    </section>
  )
}
