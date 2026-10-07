import { useMemo } from "react"
import * as THREE from "three"
import type { StarfieldProps } from "../types"

export function Starfield({
  count = 2000,
  radius = 120,
  opacity = 0.6,
}: StarfieldProps) {
  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry()
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const r = radius * 0.6 + Math.random() * radius * 0.4
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      pos[i * 3 + 2] = r * Math.cos(phi)
    }
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3))
    return g
  }, [count, radius])

  return (
    <points geometry={geometry}>
      <pointsMaterial color="#ffffff" size={0.5} transparent opacity={opacity} sizeAttenuation />
    </points>
  )
}
