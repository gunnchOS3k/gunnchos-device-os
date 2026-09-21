import type { ReactNode } from 'react'
import Icon from '../icons/Icon'
import type { VxpIconName } from '../tokens'

export function EmptyState({
  title,
  detail,
  icon = 'empty',
}: {
  title: string
  detail?: string
  icon?: VxpIconName
}) {
  return (
    <div className="cx2-empty vxp-empty" role="status">
      <Icon name={icon} size={28} className="vxp-empty-icon" />
      <strong className="vxp-empty-title">{title}</strong>
      {detail ? <p className="vxp-empty-detail">{detail}</p> : null}
    </div>
  )
}

export function SurfaceHeader({
  titleId,
  title,
  lead,
  meta,
}: {
  titleId: string
  title: string
  lead?: ReactNode
  meta?: ReactNode
}) {
  return (
    <header className="vxp-surface-header">
      <h1 id={titleId}>{title}</h1>
      {lead ? <p className="lead">{lead}</p> : null}
      {meta ? <div className="vxp-surface-meta">{meta}</div> : null}
    </header>
  )
}
