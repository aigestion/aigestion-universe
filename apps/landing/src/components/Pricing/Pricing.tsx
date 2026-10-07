const tiers = [
  {
    name: 'Local',
    price: '0',
    cadence: 'forever',
    desc: 'Full Daniela OS on your own hardware. No account, no cloud.',
    features: ['10k tasks/month', '1 device (this PC)', 'Local LLM only', 'Episodic memory tier', 'MIT licensed'],
    cta: 'Download Free',
    accent: false,
  },
  {
    name: 'Pro',
    price: '29',
    cadence: '/user/mo',
    desc: 'Multi-device sync, cloud LLM routing, swarm orchestration.',
    features: ['Unlimited tasks', 'Phone + PC + Server', 'BYOK cloud models', 'All 3 memory tiers', 'Priority consensus', "God's Eye View"],
    cta: 'Start Pro Trial',
    accent: true,
  },
  {
    name: 'Enterprise',
    price: '199',
    cadence: '/user/mo',
    desc: 'FIPS 140-3, HSM keys, SSO, audit trails, on-prem support.',
    features: ['FIPS 140-3 L3 + HSM', 'SSO / SAML / SCIM', 'Merkle audit log', 'Post-quantum hybrid', '99.9% SLA', 'Dedicated support'],
    cta: 'Contact Sales',
    accent: false,
  },
]

export function Pricing() {
  return (
    <section id="pricing" className="relative py-24 md:py-32 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-display font-light tracking-tight mb-6">
            Simple, <span className="text-gradient">honest pricing</span>
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            BYOK with zero markup. We never touch your tokens.
            Price-match any competitor +10%.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {tiers.map((t) => (
            <div
              key={t.name}
              className={`glass rounded-3xl p-8 flex flex-col ${t.accent ? 'neural-glow border-cyan-400/40 md:-translate-y-4' : ''}`}
            >
              <div className="text-sm font-mono text-gray-500 uppercase tracking-wider mb-2">{t.name}</div>
              <div className="flex items-baseline gap-1 mb-1">
                <span className="text-5xl font-display font-light">${t.price}</span>
                <span className="text-sm text-gray-500">{t.cadence}</span>
              </div>
              <p className="text-sm text-gray-400 mb-6 leading-relaxed">{t.desc}</p>
              <ul className="space-y-3 text-sm text-gray-300 mb-8 flex-1">
                {t.features.map((f) => (
                  <li key={f} className="flex gap-2">
                    <span className={t.accent ? 'text-cyan-400' : 'text-green-400'}>✓</span> {f}
                  </li>
                ))}
              </ul>
              <a href={t.accent ? '#cta' : '/download'} className={t.accent ? 'btn-primary text-center' : 'btn-secondary text-center'}>
                {t.cta}
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
