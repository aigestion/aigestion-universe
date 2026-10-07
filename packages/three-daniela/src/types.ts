export type Quality = "low" | "medium" | "high"

export interface NeuralParticlesProps {
  count?: number
  radius?: number
  colorA?: string
  colorB?: string
  repulsionStrength?: number
  repulsionRadius?: number
  mouse?: { x: number; y: number } | null
}

export interface CoreOrbProps {
  radius?: number
  color?: string
  emissiveIntensity?: number
}

export interface OrbitRingsProps {
  count?: number
  baseRadius?: number
  gap?: number
  colors?: string[]
  speed?: number
}

export interface StarfieldProps {
  count?: number
  radius?: number
  opacity?: number
}
