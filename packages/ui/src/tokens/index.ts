/** Neural design tokens for Daniela OS. */
export const colors = {
  bg: "#01050e",
  panel: "#0a0a1a",
  cyan: "#00f0ff",
  magenta: "#e024c3",
  green: "#00ff66",
  amber: "#ffb300",
  red: "#ff2f6d",
  text: "#e5e5e5",
  muted: "#6b7280",
} as const

export type ColorName = keyof typeof colors

export const radius = {
  sm: "8px",
  md: "12px",
  lg: "20px",
  xl: "28px",
} as const

export const spacing = {
  xs: "4px",
  sm: "8px",
  md: "16px",
  lg: "24px",
  xl: "32px",
} as const

export const fonts = {
  mono: "'JetBrains Mono', 'Fira Code', monospace",
  sans: "'Geist', 'Inter', system-ui, sans-serif",
} as const
