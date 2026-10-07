import type { Config } from 'tailwindcss'
const config = {
  content: ['./src/pages/**/*.{js,ts,jsx,tsx,mdx}', './src/components/**/*.{js,ts,jsx,tsx,mdx}', './src/app/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        neural: { bg: '#01050e', panel: '#0a0a1a', cyan: '#00f0ff', magenta: '#e024c3', green: '#00ff66', amber: '#ffb300', red: '#ff2f6d' }
      },
      fontFamily: { mono: ['JetBrains Mono', 'Fira Code', 'monospace'], sans: ['Geist', 'Inter', 'system-ui', 'sans-serif'], display: ['Geist Display', 'Cal Sans', 'sans-serif'] },
      animation: { 'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite', 'float': 'float 6s ease-in-out infinite', 'glow': 'glow 2s ease-in-out infinite alternate' },
      keyframes: { float: { '0%, 100%': { transform: 'translateY(0px)' }, '50%': { transform: 'translateY(-20px)' } }, glow: { '0%': { boxShadow: '0 0 20px rgba(0, 240, 255, 0.3)' }, '100%': { boxShadow: '0 0 40px rgba(224, 36, 195, 0.5)' } } }
    },
  },
  plugins: [],
}
export default config
