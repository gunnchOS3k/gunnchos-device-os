import { useMemo, useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'
import { searchWiredIndex, type SearchHit } from '../platform/searchIndex'
import type { Cx2Surface } from '../shellSurfaces'
import type { SettingsSectionId } from './SettingsSurface'

export default function SearchCommandSurface({
  onNavigate,
  onOpenSettingsSection,
}: {
  onNavigate: (id: Cx2Surface) => void
  onOpenSettingsSection?: (section: SettingsSectionId) => void
}) {
  const [query, setQuery] = useState('')
  const hits = useMemo(() => searchWiredIndex(query), [query])

  const activate = (hit: SearchHit) => {
    if (hit.kind === 'setting' && hit.settingSection && onOpenSettingsSection) {
      onOpenSettingsSection(hit.settingSection as SettingsSectionId)
      return
    }
    onNavigate(hit.surface)
  }

  return (
    <section className="cx2-panel vxp-search-command" aria-labelledby="cx2-search-title">
      <SurfaceHeader
        titleId="cx2-search-title"
        title="Search / Command"
        lead="System-wide find across wired surfaces, library entries, settings sections, and commands. Nothing fabricated."
      />
      <div className="vxp-search-row">
        <label htmlFor="system-search">Search gunnchOS</label>
        <input
          id="system-search"
          className="cx2-field"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Search gunnchOS"
          data-testid="system-search"
          autoFocus
        />
      </div>
      {hits.length === 0 ? (
        <EmptyState icon="search" title="No wired matches" detail="We only index destinations that exist in this shell." />
      ) : (
        <ul className="cx2-list vxp-search-hits" aria-label="Search results">
          {hits.map((h) => (
            <li key={h.id} className="cx2-row vxp-search-hit">
              <button type="button" className="vxp-space-card" onClick={() => activate(h)}>
                <Icon name="search" size={18} />
                <span className="vxp-space-label">{h.title}</span>
                <span className="vxp-space-purpose">
                  {h.kind} · {h.detail}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
