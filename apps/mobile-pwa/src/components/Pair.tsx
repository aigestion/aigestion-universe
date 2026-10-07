import { useEffect, useRef, useState } from "react"
import { QrCode, RefreshCw, CheckCircle2, Loader2 } from "lucide-react"
import QRCode from "qrcode.react"

type Phase = "idle" | "waiting" | "paired" | "error"

export function Pair() {
  const [phase, setPhase] = useState<Phase>("idle")
  const [challenge, setChallenge] = useState("")
  const [pairCode, setPairCode] = useState("")
  const [error, setError] = useState("")
  const timer = useRef<number | null>(null)

  const startPairing = async () => {
    setPhase("waiting")
    setError("")
    try {
      // Request a pairing challenge from the Termux edge gateway
      const res = await fetch("/api/pair/challenge", { method: "POST" })
      if (!res.ok) throw new Error("challenge failed")
      const data = await res.json()
      setChallenge(data.challenge)
      setPairCode(data.pair_code)
    } catch {
      setPhase("error")
      setError("Gateway unreachable. Is the Termux edge service running?")
    }
  }

  useEffect(() => () => { if (timer.current) clearInterval(timer.current) }, [])

  return (
    <div className="p-4 space-y-4">
      <header>
        <div className="text-xs font-mono text-neural-cyan">PC ↔ PIXEL</div>
        <h1 className="text-2xl font-display font-light">Pair device</h1>
        <p className="text-xs text-gray-500 mt-1">
          Challenge-response pairing. Scan the QR on your PC, or enter the code on the PC terminal.
        </p>
      </header>

      {phase === "idle" && (
        <button onClick={startPairing} className="btn-primary w-full py-4 rounded-2xl">
          Start pairing
        </button>
      )}

      {phase === "waiting" && (
        <div className="glass-strong rounded-2xl p-6 text-center space-y-4">
          <div className="flex justify-center">
            <div className="bg-white p-3 rounded-2xl">
              <QRCode value={pairCode || challenge} size={180} fgColor="#01050e" level="M" />
            </div>
          </div>
          <div>
            <div className="text-[10px] font-mono text-gray-500">PAIR CODE</div>
            <div className="text-2xl font-mono tracking-[0.3em] text-neural-cyan">{pairCode || "····"}</div>
          </div>
          <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
            <Loader2 size={14} className="animate-spin" /> Waiting for PC confirmation…
          </div>
          <button onClick={startPairing} className="btn-ghost text-xs">
            <RefreshCw size={12} className="inline mr-1" /> Regenerate
          </button>
        </div>
      )}

      {phase === "paired" && (
        <div className="glass-strong rounded-2xl p-6 text-center space-y-2 border-neural-green/40">
          <CheckCircle2 size={40} className="text-neural-green mx-auto" />
          <div className="text-lg font-semibold text-neural-green">Paired</div>
          <div className="text-xs text-gray-500">This phone is now linked to your PC.</div>
        </div>
      )}

      {phase === "error" && (
        <div className="glass rounded-2xl p-4 border-neural-red/40 text-sm text-neural-red">{error}</div>
      )}
    </div>
  )
}
