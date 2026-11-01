import { cva, type VariantProps } from 'class-variance-authority'
import type { ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/utils'

const button = cva(
  'inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 text-sm font-semibold transition-colors disabled:opacity-50',
  {
    variants: {
      variant: {
        primary: 'bg-accent text-accent-fg hover:brightness-110',
        secondary: 'border border-line bg-surface-2 text-fg hover:brightness-110',
        ghost: 'text-muted hover:text-fg',
        danger: 'border border-danger text-danger hover:bg-surface-2'
      }
    },
    defaultVariants: { variant: 'secondary' }
  }
)

type Props = ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof button>

export function Button({ variant, className, ...props }: Props): React.JSX.Element {
  return (
    <button
      type="button"
      data-variant={variant ?? 'secondary'}
      className={cn(button({ variant }), className)}
      {...props}
    />
  )
}
