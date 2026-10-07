import type { Metadata, Viewport } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-sans', display: 'swap' })
const jetbrainsMono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono', display: 'swap' })

export const metadata: Metadata = {
  title: 'aigestion.net | Orchestrate 19 AI engines. Zero cloud cost. Your infrastructure.',
  description: 'Daniela OS - Autonomous AI Service Management & Edge Orchestrator. 19 federated engines, neural core, edge deployment, zero cloud cost.',
  keywords: ['AI orchestration', 'edge computing', 'autonomous agents', 'Daniela OS', 'self-hosted AI', 'privacy-first AI'],
  authors: [{ name: 'AIGESTION Team' }],
  creator: 'AIGESTION',
  publisher: 'AIGESTION',
  robots: { index: true, follow: true },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://aigestion.net',
    title: 'aigestion.net | Orchestrate 19 AI engines. Zero cloud cost.',
    description: 'Daniela OS - Your personal AI, renamed by you. Runs on phone, desktop, server.',
    siteName: 'aigestion.net',
  },
  twitter: { card: 'summary_large_image', title: 'aigestion.net', description: 'Orchestrate 19 AI engines. Zero cloud cost.' },
  verification: { google: 'google-site-verification-code' },
}

export const viewport: Viewport = {
  themeColor: '#01050e',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href="https://api.aigestion.net" />
        <link rel="preload" as="font" href="/fonts/GeistVF.woff2" type="font/woff2" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen bg-neural-bg font-sans antialiased">
        {children}
      </body>
    </html>
  )
}
