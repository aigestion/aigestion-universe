import { useEffect, useState } from "react"
import { Database, Layers } from "lucide-react"

interface Tier { name: string; count: number; color: string }

const DEFAULTS: Tier[] = [
  { name: "episodic", count: 4210, color: "text-neural-cyan" },
  { name: "semantic", count: 6180, color: "text-neural-magenta" },
  { name: "procedural", count: 2090, color: "text-neural-green" },
]

export function Memory() {
  const [tiers] = useState<Tier[]>(DEFAULTS)

  useEffect(() => {
    // TODO: fetch /api/v1/memory/stats
  }, [])

  const total = tiers.reduce((a, t) => a + t.count, 0)

  return (
    <div className="p-4 space-y-4">
      <header className="flex items-center justify-between">
        <div>
          <div className="text-xs font-mono text-neural-cyan">VAULT</div>
          <h1 className="text-2xl font-display font-light">Memory</h1>
        </div>
        <Database size={22} className="text-neural-cyan" />
      </header>

      <div className="glass rounded-2xl p-4">
        <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
          <Layers size={14} /> TOTAL NODES
        </div>
        <div className="text-3xl font-mono font-light">{total.toLocaleString()}</div>
      </div>

      <div className="space-y-2">
        {tiers.map((t) => {
          const pct = total ? (t.count / total) * 100 : 0
          return (
            <div key={t.name} className="glass rounded-xl p-3">
              <div className="flex items-center justify-between mb-2">
                <span className={`text-sm font-mono ${t.color}`}>{t.name}</span>
                <span className="text-xs font-mono text-gray-400">{t.count.toLocaleString()}</span>
              </div>
              <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-neural-cyan to-neural-magenta"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
