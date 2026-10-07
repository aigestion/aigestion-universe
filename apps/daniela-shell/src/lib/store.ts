import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { Quality } from "@aigestion/three-daniela"

export type Section =
  | "brain" | "orchestrator" | "agents" | "life"
  | "voice" | "tools" | "admin" | "settings"

interface ShellState {
  personaName: string
  activeSection: Section
  quality: Quality
  particleCount: number
  autoRotate: boolean
  apiUrl: string
  setActiveSection: (s: Section) => void
  setQuality: (q: Quality) => void
  setPersona: (name: string) => void
  toggleAutoRotate: () => void
}

export const useShellStore = create<ShellState>()(
  persist(
    (set) => ({
      personaName: "Daniela",
      activeSection: "brain",
      quality: "high",
      particleCount: 12000,
      autoRotate: true,
      apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:9200",
      setActiveSection: (activeSection) => set({ activeSection }),
      setQuality: (quality) =>
        set({
          quality,
          particleCount: quality === "high" ? 12000 : quality === "medium" ? 6000 : 2000,
        }),
      setPersona: (personaName) => set({ personaName }),
      toggleAutoRotate: () => set((s) => ({ autoRotate: !s.autoRotate })),
    }),
    {
      name: "daniela-shell",
      partialize: (s) => ({
        personaName: s.personaName,
        quality: s.quality,
        autoRotate: s.autoRotate,
      }),
    }
  )
)
