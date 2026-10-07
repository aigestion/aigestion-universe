import { Routes, Route } from "react-router-dom"
import { Home } from "./components/Home"
import { Pair } from "./components/Pair"
import { Engines } from "./components/Engines"
import { Memory } from "./components/Memory"
import { BottomNav } from "./components/BottomNav"

export default function App() {
  return (
    <div className="min-h-dvh flex flex-col">
      <main className="flex-1 pb-20">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/pair" element={<Pair />} />
          <Route path="/engines" element={<Engines />} />
          <Route path="/memory" element={<Memory />} />
        </Routes>
      </main>
      <BottomNav />
    </div>
  )
}
