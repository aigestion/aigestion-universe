const DEFAULT_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9200"

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${DEFAULT_API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  return res.json() as Promise<T>
}

export const api = {
  brain: {
    process: (input: string, context?: Record<string, unknown>) =>
      req("/api/v1/brain/process", { method: "POST", body: JSON.stringify({ input, context }) }),
    stats: () => req("/api/v1/brain/stats"),
  },
  memory: {
    store: (tier: string, content: string, importance = 0.5) =>
      req("/api/v1/memory/store", { method: "POST", body: JSON.stringify({ tier, content, importance }) }),
    recall: (query: string, limit = 10) =>
      req("/api/v1/memory/recall", { method: "POST", body: JSON.stringify({ query, limit }) }),
    stats: () => req("/api/v1/memory/stats"),
  },
  orchestrator: {
    delegate: (description: string, payload?: Record<string, unknown>) =>
      req("/api/v1/orchestrator/delegate", { method: "POST", body: JSON.stringify({ description, payload }) }),
    engines: () => req("/api/v1/orchestrator/engines"),
    stats: () => req("/api/v1/orchestrator/stats"),
  },
  persona: {
    me: () => req("/api/v1/persona/me"),
    greet: () => req("/api/v1/persona/greet"),
    rename: (name: string) =>
      req("/api/v1/persona/rename", { method: "POST", body: JSON.stringify({ name }) }),
  },
  agents: { list: () => req("/api/v1/agents/list") },
  tools: { list: () => req("/api/v1/tools/list"), providers: () => req("/api/v1/tools/providers") },
  health: () => req("/health"),
}

export type { }
