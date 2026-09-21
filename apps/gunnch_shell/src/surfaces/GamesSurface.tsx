import { useCallback, useEffect, useState } from 'react'
import Icon from '../design/icons/Icon'
import { EmptyState, SurfaceHeader } from '../design/primitives/SurfaceChrome'
import { GAME_TITLES } from '../platform/appLibraryCatalog'
import { capsuleInvoke, isCapsuleBridgeAvailable } from '../platform/capsuleBridge'
import { listContinuity, recordContinuity } from '../platform/continuityStore'

type GameRow = {
  id: string
  title: string
  preferred: string
  installState: string
  lastPlayed?: string
}

export default function GamesSurface({
  onError,
}: {
  onError: (msg: string | null) => void
}) {
  const [games, setGames] = useState<GameRow[]>([])
  const [busyId, setBusyId] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const continuity = listContinuity().filter((c) => c.domain === 'game')
    let rows: GameRow[] = GAME_TITLES.map((g) => ({
      id: g.gameId || g.id,
      title: g.name,
      preferred: 'CAPSULE_WEB',
      installState: g.installState,
      lastPlayed: continuity.find((c) => c.payload?.gameId === (g.gameId || g.id))?.updatedAt,
    }))
    if (isCapsuleBridgeAvailable()) {
      const res = await capsuleInvoke('games_list')
      if (res.ok && res.result && typeof res.result === 'object') {
        const matrix = res.result as Record<string, Record<string, unknown>>
        rows = rows.map((r) => {
          const m = matrix[r.id]
          if (!m) return r
          return {
            ...r,
            title: String(m.title || r.title),
            preferred: String(m.preferred || r.preferred),
            installState: m.capsuleWeb ? 'available' : 'unavailable',
          }
        })
      }
      onError(null)
    }
    setGames(rows)
  }, [onError])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const launch = async (game: GameRow, continuePlay: boolean) => {
    setBusyId(game.id)
    try {
      if (isCapsuleBridgeAvailable()) {
        const res = await capsuleInvoke('games_launch', { id: game.id, mode: game.preferred })
        if (!res.ok) {
          onError(res.error || 'Launch failed')
          return
        }
        const result = (res.result || {}) as Record<string, unknown>
        if (String(result.mode) === 'UNAVAILABLE') {
          onError(String(result.reason || 'Game build not present on this device'))
        } else {
          onError(null)
        }
      } else {
        onError(null)
      }
      recordContinuity({
        id: `game-${game.id}`,
        domain: 'game',
        title: game.title,
        subtitle: continuePlay ? 'Continue' : 'Launch',
        surface: 'games',
        payload: { gameId: game.id },
      })
      await refresh()
    } finally {
      setBusyId(null)
    }
  }

  return (
    <section className="cx2-panel vxp-games" aria-labelledby="cx2-games-title" data-testid="games-surface">
      <SurfaceHeader
        titleId="cx2-games-title"
        title="Games"
        lead="First-party library. Titles and install honesty only — no repo or SHA in the UI."
      />
      {games.length === 0 ? (
        <EmptyState icon="empty" title="No games wired" detail="The first-party catalog is empty." />
      ) : (
        <ul className="cx2-list vxp-app-list" aria-label="Games library">
          {games.map((g) => (
            <li key={g.id} className="cx2-row vxp-app-row" data-game-id={g.id}>
              <div className="vxp-app-identity">
                <span className="vxp-app-glyph" aria-hidden="true">
                  <Icon name="app_glyph" size={28} />
                </span>
                <div>
                  <strong>{g.title}</strong>
                  <div className="vxp-app-status">
                    {g.installState === 'unavailable' ? 'Unavailable' : 'Ready when build present'} · {g.preferred}
                    {g.lastPlayed ? ` · played ${new Date(g.lastPlayed).toLocaleString()}` : ''}
                  </div>
                </div>
              </div>
              <div className="cx2-actions">
                <button
                  type="button"
                  className="cx2-action primary"
                  disabled={busyId === g.id}
                  onClick={() => void launch(g, false)}
                >
                  <Icon name="open" size={16} />
                  <span>Launch</span>
                </button>
                {g.lastPlayed && (
                  <button
                    type="button"
                    className="cx2-action"
                    disabled={busyId === g.id}
                    onClick={() => void launch(g, true)}
                  >
                    Continue
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
