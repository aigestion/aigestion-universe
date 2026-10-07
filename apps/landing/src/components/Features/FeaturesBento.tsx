const features = [
  {
    title: 'Swarm Orchestration',
    desc: '19 federated engines coordinated by Raft consensus. Cross-engine gateway routes any task to the right engine in <30ms.',
    icon: '⚡',
    accent: 'cyan',
    span: 'md:col-span-2',
  },
  {
    title: 'Neural Core',
    desc: 'Daniela OS runs 12,480 memory nodes across 3 tiers: Episodic, Semantic, Procedural. Coherent Level 4.',
    icon: '🧠',
    accent: 'magenta',
    span: '',
  },
  {
    title: 'Edge Native',
    desc: 'Runs on your Pixel, your PC, your k3s cluster. Zero cloud. Your data never leaves your metal.',
    icon: '📱',
    accent: 'green',
    span: '',
  },
  {
    title: 'God\'s Eye View',
    desc: 'Unified observability: every engine, every agent, every memory node in one holographic dashboard.',
    icon: '👁',
    accent: 'cyan',
    span: '',
  },
  {
    title: 'Voice + Vision',
    desc: 'TTS/STT on-device. Camera and screen perception. Termux API gateway exposes 30 endpoints.',
    icon: '🎙',
    accent: 'magenta',
    span: '',
  },
  {
    title: 'BYOK, Zero Markup',
    desc: 'Bring your own key. We never mark up token costs. Free tier covers 10k tasks/month locally.',
    icon: '🔑',
    accent: 'green',
    span: 'md:col-span-2',
  },
]

const accents: Record<string, string> = {
  cyan: 'from-cyan-500/20 to-cyan-500/0 border-cyan-500/30',
  magenta: 'from-fuchsia-500/20 to-fuchsia-500/0 border-fuchsia-500/30',
  green: 'from-emerald-500/20 to-emerald-500/0 border-emerald-500/30',
}

export function FeaturesBento() {
  return (
    <div className="grid md:grid-cols-3 gap-4">
      {features.map((f) => (
        <div
          key={f.title}
          className={glass rounded-2xl p-6 bg-gradient-to-b  border hover:neural-glow transition-all duration-300 }
        >
          <div className="text-3xl mb-4">{f.icon}</div>
          <h3 className="text-xl font-display font-medium text-white mb-2">{f.title}</h3>
          <p className="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
        </div>
      ))}
    </div>
  )
}
