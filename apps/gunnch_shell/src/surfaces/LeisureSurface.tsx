import { useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'
import { recordContinuity } from '../platform/continuityStore'

type LeisureItem = {
  id: string
  title: string
  kind: 'ambient' | 'reading' | 'local_audio'
  note: string
}

const CATALOG: LeisureItem[] = [
  {
    id: 'breath',
    title: 'Quiet breath timer',
    kind: 'ambient',
    note: 'Local timer only — no streaming.',
  },
  {
    id: 'reading',
    title: 'Reading shelf',
    kind: 'reading',
    note: 'Open documents you already own in Vault. No unlicensed catalog.',
  },
  {
    id: 'local-audio',
    title: 'Local audio session',
    kind: 'local_audio',
    note: 'Play files you import. Capsule does not ship licensed music streams.',
  },
]

export default function LeisureSurface({
  onNavigateVault,
}: {
  onNavigateVault: () => void
}) {
  const [active, setActive] = useState<string | null>(null)
  const [seconds, setSeconds] = useState(60)

  const start = (item: LeisureItem) => {
    setActive(item.id)
    recordContinuity({
      id: `leisure-${item.id}`,
      domain: 'leisure',
      title: item.title,
      subtitle: item.kind,
      surface: 'leisure',
    })
    if (item.kind === 'reading') onNavigateVault()
  }

  return (
    <section className="cx2-panel vxp-leisure" aria-labelledby="cx2-leisure-title" data-testid="leisure-surface">
      <SurfaceHeader
        titleId="cx2-leisure-title"
        title="Leisure"
        lead="Intentional rest and rights-safe media. No unlicensed streaming is offered or implied."
      />
      <ul className="cx2-list vxp-app-list" aria-label="Leisure activities">
        {CATALOG.map((item) => (
          <li key={item.id} className="cx2-row vxp-app-row">
            <div className="vxp-app-identity">
              <span className="vxp-app-glyph" aria-hidden="true">
                <Icon name="care" size={28} />
              </span>
              <div>
                <strong>{item.title}</strong>
                <div className="vxp-app-status">{item.note}</div>
              </div>
            </div>
            <button type="button" className="cx2-action primary" onClick={() => start(item)}>
              Open
            </button>
          </li>
        ))}
      </ul>

      {active === 'breath' && (
        <div className="vxp-leisure-session" role="status">
          <p>
            Breath timer: {seconds}s (local). Adjust and sit — nothing is streamed.
          </p>
          <input
            type="range"
            min={30}
            max={300}
            step={30}
            value={seconds}
            onChange={(e) => setSeconds(Number(e.target.value))}
            aria-label="Breath timer seconds"
          />
        </div>
      )}

      {active === 'local-audio' && (
        <EmptyState
          icon="status_warn"
          title="Import required"
          detail="Add your own audio via Vault or device files. Capsule will not invent a streaming catalog."
        />
      )}
    </section>
  )
}
