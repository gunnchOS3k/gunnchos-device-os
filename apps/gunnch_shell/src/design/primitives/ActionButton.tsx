import type { ButtonHTMLAttributes, ReactNode } from 'react'
import Icon from '../icons/Icon'
import type { VxpIconName } from '../tokens'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost'
  icon?: VxpIconName
  children: ReactNode
}

export function ActionButton({ variant = 'secondary', icon, children, className, ...rest }: Props) {
  const cls = ['cx2-action', variant === 'primary' ? 'primary' : '', className].filter(Boolean).join(' ')
  return (
    <button type="button" className={cls} {...rest}>
      {icon ? <Icon name={icon} size={18} /> : null}
      <span>{children}</span>
    </button>
  )
}
