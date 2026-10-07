export function Footer() {
  const year = new Date().getFullYear()
  const cols = [
    { title: 'Product', links: ['Neural Shell', 'Daniela OS', 'GEV Dashboard', 'Edge Gateway', 'Robotics'] },
    { title: 'Developers', links: ['Docs', 'API Reference', 'MCP Tools', 'OpenAPI Spec', 'Status'] },
    { title: 'Company', links: ['Manifesto', 'Security', 'Privacy', 'Blog', 'Careers'] },
    { title: 'Legal', links: ['MIT License', 'Terms', 'DPA', 'Responsible AI'] },
  ]
  return (
    <footer className="border-t border-white/5 bg-neural-panel/30">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-6 gap-10">
          <div className="md:col-span-2">
            <div className="text-2xl font-display font-light mb-4">
              aigestion<span className="text-cyan-400">.net</span>
            </div>
            <p className="text-sm text-gray-500 leading-relaxed mb-6">
              Autonomous AI Service Management & Edge Orchestrator.
              19 federated engines. Swarm intelligence. Runs on your metal.
            </p>
            <div className="flex items-center gap-2 text-xs font-mono text-green-400">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
              ALL SYSTEMS OPERATIONAL
            </div>
          </div>
          {cols.map((c) => (
            <div key={c.title}>
              <div className="text-xs font-mono text-gray-500 uppercase tracking-wider mb-4">{c.title}</div>
              <ul className="space-y-2">
                {c.links.map((l) => (
                  <li key={l}>
                    <a href="#" className="text-sm text-gray-400 hover:text-cyan-400 transition-colors">{l}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="border-t border-white/5 mt-12 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-600">© {year} AIGESTION. MIT License. Zero cloud cost.</p>
          <div className="flex items-center gap-6 text-xs font-mono text-gray-600">
            <span>FIPS 140-3 L3</span>
            <span>Zero-Knowledge</span>
            <span>Post-Quantum</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
