'use client'

import { useState } from 'react'

export function DemoEmbed() {
  const [playing, setPlaying] = useState(false)
  return (
    <section id="demo" className="relative py-24 px-6 max-w-5xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-4xl md:text-5xl font-display font-light tracking-tight mb-4">
          See the <span className="text-gradient">neural core</span> breathe
        </h2>
        <p className="text-gray-400 text-lg">Live telemetry from a single-board deployment. No simulation, no mock data.</p>
      </div>
      <div className="glass-strong rounded-3xl p-2 neural-glow">
        <div className="rounded-2xl overflow-hidden bg-black aspect-video relative">
          {!playing ? (
            <button
              onClick={() => setPlaying(true)}
              className="absolute inset-0 flex flex-col items-center justify-center group"
            >
              <div className="w-20 h-20 rounded-full bg-cyan-500/20 border border-cyan-400/50 flex items-center justify-center group-hover:scale-110 transition-transform">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="cyan"><path d="M8 5v14l11-7z"/></svg>
              </div>
              <span className="mt-4 text-sm font-mono text-cyan-400">PLAY LIVE TELEMETRY</span>
            </button>
          ) : (
            <iframe
              src="http://localhost:3200/embed"
              className="w-full h-full"
              title="Daniela OS live dashboard"
              sandbox="allow-scripts allow-same-origin"
            />
          )}
        </div>
        <div className="flex items-center justify-between px-4 py-3 border-t border-white/5">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
            <span className="text-xs font-mono text-gray-400">REC · GRAFANA STREAM</span>
          </div>
          <span className="text-xs font-mono text-gray-500">12,480 nodes · 19 engines · 96% empathy</span>
        </div>
      </div>
    </section>
  )
}
