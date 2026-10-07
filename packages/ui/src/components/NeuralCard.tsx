import { HTMLAttributes, forwardRef } from "react"
import { colors, radius, spacing } from "../tokens"

export interface NeuralCardProps extends HTMLAttributes<HTMLDivElement> {
  accent?: string
}

export const NeuralCard = forwardRef<HTMLDivElement, NeuralCardProps>(
  ({ accent = colors.cyan, style, children, ...rest }, ref) => (
    <div
      ref={ref}
      style={{
        background: colors.panel,
        border: `1px solid ${colors.cyan}33`,
        borderRadius: radius.lg,
        padding: spacing.md,
        ...style,
      }}
      {...rest}
    >
      {accent && (
        <div
          style={{
            width: "4px",
            height: "40px",
            borderRadius: "2px",
            background: accent,
            marginBottom: spacing.sm,
          }}
        />
      )}
      {children}
    </div>
  )
)
NeuralCard.displayName = "NeuralCard"
