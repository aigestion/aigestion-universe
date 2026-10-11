"use client"

import { useCallback, useEffect, useState } from "react"
import { AlertTriangle, CheckCircle2, ExternalLink, KeyRound, RefreshCw, XCircle } from "lucide-react"
import { api, type KeySlot } from "@/lib/api"

const STORE_KEY = "daniela-keys-rotated"

function loadRotated(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(STORE_KEY) ?? "{}")
  } catch {
    return {}
  }
}

export function KeysPanel() {
  const [slots, setSlots] = useState<KeySlot[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [rotated, setRotated] = useState<Record<string, boolean>>({})
  const [openId, setOpenId] = useState<string | null>(null)

  const fetchStatus = useCallback(async () => {
    setError(null)
    try {
      const data = await api.security.keysStatus()
      setSlots(data.slots)
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo contactar al core (:9200)")
    }
  }, [])

  useEffect(() => {
    setRotated(loadRotated())
    void fetchStatus()
  }, [fetchStatus])

  const markRotated = (id: string, value: boolean) => {
    const next = { ...rotated, [id]: value }
    setRotated(next)
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(next))
    } catch {
      /* almacenamiento no disponible: se pierde al recargar */
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="max-w-2xl mx-auto space-y-4">
        <div className="flex items-center gap-3">
          <KeyRound size={22} className="text-neural-cyan" />
          <div>
            <h2 className="text-lg font-semibold text-white">Rotación de claves API</h2>
            <p className="text-xs text-gray-400">
              El panel solo muestra si cada clave está configurada. Los valores nunca salen del servidor.
            </p>
          </div>
          <button
            onClick={() => void fetchStatus()}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-300 hover:text-white hover:bg-white/5 border border-white/10"
          >
            <RefreshCw size={14} /> Verificar
          </button>
        </div>

        <div className="flex gap-3 p-3 rounded-lg border border-amber-400/30 bg-amber-400/5 text-xs text-amber-200">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <span>
            La rotación se hace en el panel de cada proveedor. Tras actualizar el{" "}
            <code className="font-mono">.env</code> del servidor y reiniciar, pulsa Verificar y
            elimina la clave vieja. Marca cada casilla solo cuando hayas borrado la anterior.
          </span>
        </div>

        {error && (
          <div className="p-3 rounded-lg border border-red-400/30 bg-red-400/5 text-xs text-red-200">
            {error} — ¿Está el core en marcha?
          </div>
        )}

        {!slots && !error && <div className="text-sm text-gray-500">Cargando estado…</div>}

        {slots?.map((s) => {
          const done = rotated[s.id] === true
          return (
            <div key={s.id} className="rounded-lg border border-white/10 bg-white/[0.02] overflow-hidden">
              <button
                onClick={() => setOpenId(openId === s.id ? null : s.id)}
                className="w-full flex items-center gap-3 p-3 text-left"
              >
                {done ? (
                  <CheckCircle2 size={18} className="text-neural-green shrink-0" />
                ) : s.configured ? (
                  <KeyRound size={18} className="text-neural-cyan shrink-0" />
                ) : (
                  <XCircle size={18} className="text-gray-600 shrink-0" />
                )}
                <div className="min-w-0">
                  <div className="text-sm text-white">{s.label}</div>
                  <div className="text-[11px] font-mono text-gray-500 truncate">
                    {s.env.join(" · ")} — {s.configured ? "configurada" : "ausente"}
                  </div>
                </div>
              </button>

              {openId === s.id && (
                <div className="px-3 pb-3 space-y-2">
                  <ol className="text-xs text-gray-300 space-y-1 list-decimal list-inside">
                    {s.steps.map((step, i) => (
                      <li key={i}>{step}</li>
                    ))}
                  </ol>
                  <div className="flex items-center gap-2 pt-1">
                    {s.dashboard_url && (
                      <a
                        href={s.dashboard_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] text-neural-cyan border border-neural-cyan/30 hover:bg-neural-cyan/10"
                      >
                        <ExternalLink size={12} /> Abrir panel del proveedor
                      </a>
                    )}
                    <label className="flex items-center gap-1.5 text-[11px] text-gray-400 ml-auto cursor-pointer">
                      <input
                        type="checkbox"
                        checked={done}
                        onChange={(e) => markRotated(s.id, e.target.checked)}
                        className="accent-emerald-400"
                      />
                      Rotada y vieja eliminada
                    </label>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
