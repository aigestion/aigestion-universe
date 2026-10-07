import type { Config } from "tailwindcss"
const config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        neural: { bg: "#01050e", panel: "#0a0a1a", cyan: "#00f0ff", magenta: "#e024c3", green: "#00ff66", amber: "#ffb300", red: "#ff2f6d" },
      },
      fontFamily: { mono: ["JetBrains Mono", "Fira Code", "monospace"], sans: ["Geist", "Inter", "system-ui", "sans-serif"] },
    },
  },
  plugins: [],
}
export default config
