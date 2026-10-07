import { ButtonHTMLAttributes, forwardRef } from "react"
import { colors, fonts, radius, spacing } from "../tokens"

type Variant = "primary" | "secondary" | "ghost"

export interface NeuralButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
}

const styles: Record<Variant, React.CSSProperties> = {
  primary: {
    background: colors.cyan,
    color: colors.bg,
    border: "none",
    boxShadow: `0 0 20px ${colors.cyan}66`,
  },
  secondary: {
    background: "transparent",
    color: colors.cyan,
    border: `1px solid ${colors.cyan}80`,
  },
  ghost: {
    background: "transparent",
    color: colors.muted,
    border: "none",
  },
}

export const NeuralButton = forwardRef<HTMLButtonElement, NeuralButtonProps>(
  ({ variant = "primary", style, children, ...rest }, ref) => (
    <button
      ref={ref}
      style={{
        padding: `${spacing.sm} ${spacing.md}`,
        borderRadius: radius.md,
        fontFamily: fonts.sans,
        fontWeight: 600,
        fontSize: "14px",
        cursor: "pointer",
        transition: "all 0.2s ease",
        ...styles[variant],
        ...style,
      }}
      {...rest}
    >
      {children}
    </button>
  )
)
NeuralButton.displayName = "NeuralButton"
