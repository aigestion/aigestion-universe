import { useEffect, useState } from "react"
import { Activity, Heart, MemoryStick, Boxes, Zap } from "lucide-react"
import { Link } from "react-router-dom"

interface Stats { coherence: number; empathy: number; nodes: number; engines: number }

export function Home() {
  const [stats] = useState<Stats>({ coherence: 4, empathy: 0.96, nodes: 12480, engines: 19 })

  useEffect(() => {
    // TODO: fetch from daniela-core /api/v1/brain/stats
  }, [])

  const tiles = [
    { icon: Activity, label: "Coherence", value: `L${stats.coherence}`, color: "text-neural-cyan" },
    { icon: Heart, label: "Empathy", value: `${(stats.empathy * 100).toFixed(0)}%`, color: "text-neural-magenta" },
    { icon: MemoryStick, label: "Nodes", value: stats.nodes.toLocaleString(), color: "text-neural-green" },
    { icon: Boxes, label: "Engines", value: `${stats.engines}`, color: "text-neural-cyan" },
  ]

  return (
    <div className="p-4 space-y-4">
      <header>
        <div className="text-xs font-mono text-neural-cyan">DANIELA OS</div>
        <h1 className="text-2xl font-display font-light">
          Neural <span className="text-gradient">Core</span>
        </h1>
      </header>

      <div className="grid grid-cols-2 gap-3">
        {tiles.map((t) => {
          const Icon = t.icon
          return (
            <div key={t.label} className="glass rounded-2xl p-4">
              <Icon size={18} className={t.color} />
              <div className="text-[10px] font-mono text-gray-500 mt-2">{t.label}</div>
              <div className={`text-lg font-mono font-semibold ${t.color}`}>{t.value}</div>
            </div>
          )
        })}
      </div>

      <Link to="/pair" className="block glass-strong rounded-2xl p-4 neural-glow">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold">Pair a device</div>
            <div className="text-xs text-gray-500 mt-1">Connect this phone to your PC</div>
          </div>
          <Zap size={20} className="text-neural-amber" />
        </div>
      </Link>
    </div>
  )
}
