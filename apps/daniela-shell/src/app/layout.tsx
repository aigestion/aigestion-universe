import type { Metadata } from "next"
import "./globals.css"

export const metadata: Metadata = {
  title: "Daniela Shell — Neural OS",
  description: "Neural Shell for Daniela OS. Orchestrate 19 AI engines.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen w-screen overflow-hidden bg-neural-bg">{children}</body>
    </html>
  )
}
