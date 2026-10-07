import { useEffect, useState } from "react"
import { Boxes, Cpu } from "lucide-react"

interface Engine { name: string; healthy: boolean; load: number; endpoint: string }

const DEFAULTS: Engine[] = [
  { name: "core", healthy: true, load: 0.12, endpoint: "daniela:9200" },
  { name: "secure", healthy: true, load: 0.08, endpoint: "security:9999" },
  { name: "performance", healthy: true, load: 0.21, endpoint: "perf:9998" },
  { name: "automation", healthy: true, load: 0.05, endpoint: "auto:9900" },
  { name: "agent_mobile", healthy: true, load: 0.15, endpoint: "mobile:9800" },
]

export function Engines() {
  const [engines, setEngines] = useState<Engine[]>(DEFAULTS)

  useEffect(() => {
    // TODO: fetch /api/v1/orchestrator/engines
  }, [])

  return (
    <div className="p-4 space-y-3">
      <header className="flex items-center justify-between">
        <div>
          <div className="text-xs font-mono text-neural-cyan">SWARM</div>
          <h1 className="text-2xl font-display font-light">Engines</h1>
        </div>
        <Boxes size={22} className="text-neural-cyan" />
      </header>

      <div className="space-y-2">
        {engines.map((e) => (
          <div key={e.name} className="glass rounded-xl p-3 flex items-center gap-3">
            <span className={`w-2 h-2 rounded-full ${e.healthy ? "bg-neural-green" : "bg-neural-red"}`} />
            <Cpu size={16} className="text-gray-500" />
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium truncate">{e.name}</div>
              <div className="text-[10px] font-mono text-gray-500">{e.endpoint}</div>
            </div>
            <div className="text-right">
              <div className={`text-xs font-mono ${e.load > 0.7 ? "text-neural-amber" : "text-neural-green"}`}>
                {(e.load * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
