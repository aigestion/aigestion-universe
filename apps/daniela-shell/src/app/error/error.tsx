export const dynamic = 'force-dynamic'
export const generateStaticParams = () => []

import React from 'react'

const errorStyle = 'body { font-family: system-ui; background: #01050e; color: white; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; } .container { text-align: center; } h1 { color: #00f0ff; } a { color: #00f0ff; text-decoration: none; }'

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <head>
        <title>Error</title>
        <style dangerouslySetInnerHTML={{ __html: errorStyle }} />
      </head>
      <body>
        <div className="container">
          <h1>System Error</h1>
          <p>Neural shell encountered an error.</p>
          <button onClick={reset} className="btn-primary">Restart Shell</button>
        </div>
      </body>
    </html>
  )
}

export const notFound = true
