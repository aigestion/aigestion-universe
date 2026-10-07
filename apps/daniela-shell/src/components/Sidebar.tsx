"use client"

import { Brain, Boxes, Users, Heart, Mic, Wrench, Shield, Settings } from "lucide-react"
import { useShellStore } from "@/lib/store"

const nav = [
  { icon: Brain, label: "Brain", section: "brain" },
  { icon: Boxes, label: "Engines", section: "orchestrator" },
  { icon: Users, label: "Agents", section: "agents" },
  { icon: Heart, label: "Life", section: "life" },
  { icon: Mic, label: "Voice", section: "voice" },
  { icon: Wrench, label: "Tools", section: "tools" },
  { icon: Shield, label: "Security", section: "admin" },
  { icon: Settings, label: "Settings", section: "settings" },
] as const

export function Sidebar() {
  const active = useShellStore((s) => s.activeSection)
  const setActive = useShellStore((s) => s.setActiveSection)
  const persona = useShellStore((s) => s.personaName)

  return (
    <aside className="w-16 md:w-56 glass-strong border-r border-white/5 flex flex-col">
      {/* Logo / persona */}
      <div className="p-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-neural-cyan to-neural-magenta neural-glow flex items-center justify-center text-black font-bold">
            {persona.charAt(0)}
          </div>
          <div className="hidden md:block min-w-0">
            <div className="text-sm font-semibold text-white truncate">{persona}</div>
            <div className="text-[10px] font-mono text-neural-cyan">NEURAL SHELL</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {nav.map((item) => {
          const Icon = item.icon
          const isActive = active === item.section
          return (
            <button
              key={item.section}
              onClick={() => setActive(item.section)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all group ${
                isActive
                  ? "bg-neural-cyan/10 text-neural-cyan border border-neural-cyan/30"
                  : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <Icon size={18} className={isActive ? "text-neural-cyan" : "text-gray-500 group-hover:text-gray-300"} />
              <span className="hidden md:block text-sm">{item.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Status */}
      <div className="p-4 border-t border-white/5">
        <div className="hidden md:flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-neural-green animate-pulse" />
          <span className="text-[10px] font-mono text-gray-500">CORE ONLINE</span>
        </div>
      </div>
    </aside>
  )
}
