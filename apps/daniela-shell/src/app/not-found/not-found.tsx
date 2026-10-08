export const dynamic = 'force-dynamic'
export const generateStaticParams = () => []

import React from 'react'
import Link from 'next/link'

const notFoundStyle = 'body { font-family: system-ui; background: #01050e; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; } .container { text-align: center; } h1 { color: #00f0ff; } a { color: #00f0ff; text-decoration: none; }'

export default function NotFound() {
  return (
    <html lang="en">
      <head>
        <title>404</title>
        <style dangerouslySetInnerHTML={{ __html: notFoundStyle }} />
      </head>
      <body>
        <div className="container">
          <h1>404</h1>
          <p>Neural pathway not found</p>
          <Link href="/" className="btn-primary">Return to Core</Link>
        </div>
      </body>
    </html>
  )
}

export const notFound = true
