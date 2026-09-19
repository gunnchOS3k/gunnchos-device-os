import type { SVGProps } from 'react'
import type { VxpIconName } from '../tokens'
import { iconPath } from './paths'

type Props = SVGProps<SVGSVGElement> & {
  name: VxpIconName
  title?: string
  size?: number
}

/** Custom geometric icon — never use emoji as product icons. */
export default function Icon({ name, title, size = 22, className, ...rest }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : 'presentation'}
      className={className ? `vxp-icon ${className}` : 'vxp-icon'}
      {...rest}
    >
      {title ? <title>{title}</title> : null}
      <path d={iconPath(name)} />
    </svg>
  )
}
