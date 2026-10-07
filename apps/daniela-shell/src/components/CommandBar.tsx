"use client"

import { useState, useRef, useEffect } from "react"
import { Send, Terminal, Loader2 } from "lucide-react"
import { useShellStore } from "@/lib/store"

export function CommandBar() {
  const [input, setInput] = useState("")
  const [thinking, setThinking] = useState(false)
  const [lastResponse, setLastResponse] = useState("")
  const apiUrl = useShellStore((s) => s.apiUrl)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  const submit = async () => {
    const text = input.trim()
    if (!text || thinking) return
    setInput("")
    setThinking(true)
    try {
      const res = await fetch(`${apiUrl}/api/v1/brain/process`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: text, context: { source: "shell" } }),
      })
      if (res.ok) {
        const data = await res.json()
        setLastResponse(data.action?.result ?? JSON.stringify(data))
      } else {
        setLastResponse(`Error ${res.status}`)
      }
    } catch {
      setLastResponse("Core unreachable — running in offline mode")
    } finally {
      setThinking(false)
    }
  }

  return (
    <footer className="glass border-t border-white/5 p-4">
      {lastResponse && (
        <div className="mb-3 text-sm text-gray-300 font-mono truncate">
          <span className="text-neural-cyan">▸ </span>{lastResponse}
        </div>
      )}
      <div className="flex items-center gap-3">
        <div className="flex-1 flex items-center gap-2 glass-strong rounded-xl px-4 py-3 border border-neural-cyan/20 focus-within:border-neural-cyan/50 transition-colors">
          <Terminal size={16} className="text-neural-cyan shrink-0" />
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Ask Daniela anything… (or /help)"
            className="flex-1 bg-transparent outline-none text-sm placeholder:text-gray-600"
            disabled={thinking}
          />
          {thinking && <Loader2 size={16} className="animate-spin text-neural-magenta" />}
        </div>
        <button
          onClick={submit}
          disabled={thinking || !input.trim()}
          className="px-4 py-3 rounded-xl bg-neural-cyan text-black font-semibold text-sm hover:bg-cyan-300 transition-all shadow-[0_0_20px_rgba(0,240,255,.4)] disabled:opacity-40 disabled:shadow-none"
        >
          <Send size={16} />
        </button>
      </div>
    </footer>
  )
}
