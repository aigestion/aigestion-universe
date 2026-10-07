export interface DanielaClientOptions {
  baseUrl?: string
  apiKey?: string
  timeout?: number
}

export class DanielaClient {
  private baseUrl: string
  private apiKey?: string

  constructor(options: DanielaClientOptions = {}) {
    this.baseUrl = (options.baseUrl ?? "http://localhost:9200").replace(/\/$/, "")
    this.apiKey = options.apiKey
  }

  private async req<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(this.baseUrl + path, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(this.apiKey ? { Authorization: `Bearer ${this.apiKey}` } : {}),
        ...(init?.headers ?? {}),
      },
    })
    if (!res.ok) throw new Error(`Daniela API ${res.status}: ${res.statusText}`)
    return res.json() as Promise<T>
  }

  greet() { return this.req<{ greeting: string }>("/api/v1/persona/greet").then(r => r.greeting) }
  brainStats() { return this.req("/api/v1/brain/stats") }
  memoryStats() { return this.req("/api/v1/memory/stats") }
  engines() { return this.req<{ engines: unknown[] }>("/api/v1/orchestrator/engines").then(r => r.engines) }

  async process(input: string, context?: Record<string, unknown>) {
    return this.req("/api/v1/brain/process", {
      method: "POST",
      body: JSON.stringify({ input, context: context ?? {} }),
    })
  }

  async memoryStore(tier: string, content: string, importance = 0.5) {
    return this.req("/api/v1/memory/store", {
      method: "POST",
      body: JSON.stringify({ tier, content, importance }),
    })
  }

  async memoryRecall(query: string, limit = 10) {
    return this.req("/api/v1/memory/recall", {
      method: "POST",
      body: JSON.stringify({ query, limit }),
    })
  }
}
