"use client"

import { useEffect, useState } from "react"
import { Activity, Cpu, MemoryStick, Zap, Globe, Heart, Boxes } from "lucide-react"

interface Telemetry {
  coherence: number
  empathy: number
  nodes: number
  engines: number
  latencyMs: number
  uptime: number
}

export function TelemetryHUD() {
  const [t, setT] = useState<Telemetry>({
    coherence: 4, empathy: 0.96, nodes: 12480, engines: 19, latencyMs: 28, uptime: 0,
  })

  useEffect(() => {
    const id = setInterval(() => {
      setT((prev) => ({
        ...prev,
        latencyMs: 24 + Math.round(Math.random() * 12),
        uptime: prev.uptime + 1,
      }))
    }, 1000)
    return () => clearInterval(id)
  }, [])

  const tiles = [
    { icon: Activity, label: "COHERENCE", value: `L${t.coherence}`, accent: "text-neural-cyan" },
    { icon: Heart, label: "EMPATHY", value: `${(t.empathy * 100).toFixed(0)}%`, accent: "text-neural-magenta" },
    { icon: MemoryStick, label: "NODES", value: t.nodes.toLocaleString(), accent: "text-neural-green" },
    { icon: Boxes, label: "ENGINES", value: `${t.engines}`, accent: "text-neural-cyan" },
    { icon: Zap, label: "P95", value: `${t.latencyMs}ms`, accent: "text-neural-amber" },
    { icon: Globe, label: "UPTIME", value: fmtUptime(t.uptime), accent: "text-gray-300" },
  ]

  return (
    <header className="glass border-b border-white/5 px-4 py-3">
      <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
        {tiles.map((tile) => {
          const Icon = tile.icon
          return (
            <div key={tile.label} className="flex items-center gap-2.5">
              <Icon size={16} className={tile.accent} />
              <div className="min-w-0">
                <div className="text-[9px] font-mono text-gray-500 tracking-wider">{tile.label}</div>
                <div className={`text-sm font-mono font-semibold ${tile.accent}`}>{tile.value}</div>
              </div>
            </div>
          )
        })}
      </div>
    </header>
  )
}

function fmtUptime(sec: number) {
  const h = Math.floor(sec / 3600)
  const m = Math.floor((sec % 3600) / 60)
  const s = sec % 60
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`
}
