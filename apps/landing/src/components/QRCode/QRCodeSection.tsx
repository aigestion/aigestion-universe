'use client'

import { useEffect, useRef } from 'react'
import QRCode from 'qrcode.react'

export function QRCodeSection() {
  const apkUrl = 'https://aigestion.net/download/daniela.apk'
  return (
    <div className="glass-strong rounded-3xl p-8 md:p-12 grid md:grid-cols-2 gap-10 items-center">
      <div>
        <h2 className="text-3xl md:text-4xl font-display font-light tracking-tight mb-4">
          Install <span className="text-gradient">Daniela</span> on your Pixel
        </h2>
        <p className="text-gray-400 leading-relaxed mb-6">
          Native Android APK with Kotlin + Jetpack Compose. Pairs with your PC via challenge-response.
          Min SDK 24 · Target SDK 34 · Offline-first sync.
        </p>
        <ol className="space-y-3 text-sm text-gray-300">
          <li className="flex gap-3"><span className="text-cyan-400 font-mono">01</span> Scan the QR code or tap download</li>
          <li className="flex gap-3"><span className="text-cyan-400 font-mono">02</span> Allow install from unknown sources</li>
          <li className="flex gap-3"><span className="text-cyan-400 font-mono">03</span> Pair with PC through Termux gateway</li>
        </ol>
        <a href="/api/download-apk" className="btn-primary inline-block mt-8">Download APK</a>
      </div>
      <div className="flex flex-col items-center gap-4">
        <div className="bg-white p-4 rounded-2xl">
          <QRCode value={apkUrl} size={220} fgColor="#01050e" level="M" />
        </div>
        <p className="text-xs font-mono text-gray-500">aigestion.net/download/daniela.apk</p>
      </div>
    </div>
  )
}
