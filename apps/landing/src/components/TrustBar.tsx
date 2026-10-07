export function TrustBar() {
  const metrics = [
    { value: '19', label: 'Federated Engines' },
    { value: '12,480', label: 'Memory Nodes' },
    { value: '96%', label: 'Empathy Score' },
    { value: '0', label: 'Cloud Cost' },
    { value: '30ms', label: 'P95 Latency' },
    { value: '3', label: 'Memory Tiers' },
  ]
  return (
    <section className="relative border-y border-white/5 bg-neural-panel/40 backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {metrics.map((m) => (
            <div key={m.label} className="text-center">
              <div className="text-3xl md:text-4xl font-display font-light text-gradient">{m.value}</div>
              <div className="text-xs font-mono text-gray-500 mt-1 uppercase tracking-wider">{m.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
