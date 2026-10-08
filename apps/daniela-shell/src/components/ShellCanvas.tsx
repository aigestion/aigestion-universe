"use client"

import { Canvas } from "@react-three/fiber"
import { OrbitControls, AdaptiveEvents } from "@react-three/drei"
import { EffectComposer, Bloom } from "@react-three/postprocessing"
import { NeuralParticles, CoreOrb, OrbitRings, Starfield } from "@aigestion/three-daniela"
import { useShellStore } from "@/lib/store"

export function ShellCanvas() {
  const particleCount = useShellStore((s) => s.particleCount)
  const quality = useShellStore((s) => s.quality)
  const autoRotate = useShellStore((s) => s.autoRotate)

  const dpr = quality === "high" ? 2 : quality === "medium" ? 1.5 : 1

  return (
    <Canvas
      camera={{ position: [0, 0, 50], fov: 60, near: 0.1, far: 1000 }}
      dpr={[1, dpr]}
      gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
      style={{ background: "#01050e" }}
    >
      <AdaptiveEvents />

      <Starfield count={2000} radius={120} opacity={0.6} />
      <NeuralParticles
        count={particleCount}
        radius={22}
        colorA="#00f0ff"
        colorB="#e024c3"
        repulsionStrength={0.6}
        repulsionRadius={8}
      />
      <CoreOrb radius={3} color="#00f0ff" emissiveIntensity={0.5} />
      <OrbitRings count={3} baseRadius={5} gap={2} speed={0.15} />

      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#00f0ff" />
      <pointLight position={[-10, -10, -10]} intensity={1} color="#e024c3" />

      <OrbitControls
        enableDamping
        dampingFactor={0.05}
        enablePan={false}
        minDistance={20}
        maxDistance={100}
        autoRotate={autoRotate}
        autoRotateSpeed={0.2}
      />

      <EffectComposer>
        <Bloom intensity={0.8} luminanceThreshold={0.1} luminanceSmoothing={0.3} mipmapBlur />
      </EffectComposer>
    </Canvas>
  )
}
