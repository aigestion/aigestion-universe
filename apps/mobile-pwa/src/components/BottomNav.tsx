import { Home, QrCode, Boxes, Database } from "lucide-react"
import { NavLink } from "react-router-dom"

const items = [
  { to: "/", icon: Home, label: "Home" },
  { to: "/pair", icon: QrCode, label: "Pair" },
  { to: "/engines", icon: Boxes, label: "Engines" },
  { to: "/memory", icon: Database, label: "Memory" },
]

export function BottomNav() {
  return (
    <nav className="fixed bottom-0 inset-x-0 glass border-t border-white/5 z-50 safe-area-pb">
      <div className="grid grid-cols-4">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex flex-col items-center gap-1 py-2.5 text-[10px] font-mono transition-colors ${
                  isActive ? "text-neural-cyan" : "text-gray-500"
                }`
              }
            >
              <Icon size={20} />
              {item.label}
            </NavLink>
          )
        })}
      </div>
    </nav>
  )
}
