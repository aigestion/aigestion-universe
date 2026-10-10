// Unified Dashboard Stores - Reactive state management

import { writable, derived, get } from 'svelte/store'

// Service configuration
export const SERVICES = [
  { id: 'epic_pc', name: 'Epic PC', port: 5020, category: 'Core' },
  { id: 'daniela', name: 'Daniela', port: 9200, category: 'AI' },
  { id: 'hermes', name: 'Hermes', port: 9300, category: 'AI' },
  { id: 'optimization', name: 'AIG Optimization', port: 9400, category: 'Infra' },
  { id: 'frontend_v1', name: 'Frontend V1', port: 9500, category: 'Frontend' },
  { id: 'frontend_v2', name: 'Frontend V2', port: 9600, category: 'Frontend' },
  { id: 'infra', name: 'Infra Optimization', port: 9700, category: 'Infra' },
  { id: 'agent_mobile', name: 'Agent & Mobile', port: 9800, category: 'AI' },
  { id: 'security', name: 'Security & Monitoring', port: 9999, category: 'Security' },
  { id: 'perf', name: 'Performance & Quality', port: 9998, category: 'Perf' },
]

// Derived stores
export const serviceStatus = writable({})
export const serviceMetrics = writable({})
export const wsConnected = writable(false)
export const lastUpdate = writable(null)
export const selectedService = writable(null)

// Health status helpers
export function getStatusClass(status) {
  if (!status) return 'offline'
  if (status === 'online' || status === 'alive') return 'online'
  if (status === 'degraded') return 'degraded'
  return 'offline'
}

export function getStatusLabel(status) {
  if (!status) return 'Unknown'
  if (status === 'online' || status === 'alive') return 'Online'
  if (status === 'degraded') return 'Degraded'
  return 'Offline'
}

// Service URL builder
export function getServiceUrl(service, path = '') {
  return `http://localhost:${service.port}${path}`
}

// Fetch all service statuses
export async function fetchAllStatuses() {
  const results = {}
  await Promise.all(
    SERVICES.map(async (svc) => {
      try {
        const res = await fetch(`http://localhost:${svc.port}/api/status`, { 
          signal: AbortSignal.timeout(3000) 
        })
        if (res.ok) {
          const data = await res.json()
          results[svc.id] = { ...data, status: 'online', port: svc.port }
        } else {
          results[svc.id] = { status: 'offline', port: svc.port }
        }
      } catch {
        results[svc.id] = { status: 'offline', port: svc.port }
      }
    })
  )
  serviceStatus.set(results)
  lastUpdate.set(new Date())
  return results
}

// WebSocket connection
export let ws = null

export function connectWebSocket() {
  if (ws && ws.readyState === WebSocket.OPEN) return
  
  // Connect to the first available service with WebSocket
  // For now, we'll poll instead of WebSocket
  wsConnected.set(false)
  
  // Start polling
  startPolling()
}

export function startPolling(interval = 5000) {
  fetchAllStatuses()
  const timer = setInterval(fetchAllStatuses, interval)
  return () => clearInterval(timer)
}

// Initialize
if (typeof window !== 'undefined') {
  connectWebSocket()
}