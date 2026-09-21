import type { Cx2Surface } from '../CompleteExperienceShell'

export default function HomeSurface({
  offline,
  onNavigate,
}: {
  offline?: boolean
  onNavigate: (id: Cx2Surface) => void
}) {
  return (
    <section className="cx2-panel" aria-labelledby="cx2-home-title">
      <h1 id="cx2-home-title">gunnch Home</h1>
      <p className="lead">
        One place for Vault, Wallet, Portfolio, Career, Verifier, App Center, Connect, Assist, and Care.
        {offline ? ' Offline mode is on — local work continues.' : ''}
      </p>
      <div className="cx2-actions" role="group" aria-label="Home shortcuts">
        <button type="button" className="cx2-action primary" onClick={() => onNavigate('vault')}>Open Vault</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('wallet')}>Wallet</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('portfolio')}>Portfolio</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('career')}>Career</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('verifier')}>Verifier</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('app_center')}>App Center</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('connect')}>Connect</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('assist')}>Assist</button>
        <button type="button" className="cx2-action" onClick={() => onNavigate('care')}>Care</button>
      </div>
    </section>
  )
}
