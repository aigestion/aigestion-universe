"use client"

import { ShellCanvas } from "@/components/ShellCanvas"
import { Sidebar } from "@/components/Sidebar"
import { TelemetryHUD } from "@/components/TelemetryHUD"
import { CommandBar } from "@/components/CommandBar"

export default function ShellPage() {
  return (
    <div className="relative h-screen w-screen scanlines">
      {/* 3D neural background */}
      <div className="absolute inset-0">
        <ShellCanvas />
      </div>

      {/* Layout grid */}
      <div className="relative z-10 flex h-full">
        <Sidebar />
        <main className="flex-1 flex flex-col min-w-0">
          <TelemetryHUD />
          <div className="flex-1" />
          <CommandBar />
        </main>
      </div>
    </div>
  )
}
