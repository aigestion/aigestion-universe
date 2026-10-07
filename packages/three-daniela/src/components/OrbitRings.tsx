import { useRef } from "react"
import { useFrame } from "@react-three/fiber"
import * as THREE from "three"
import type { OrbitRingsProps } from "../types"

const DEFAULT_COLORS = ["#00f0ff", "#e024c3", "#00ff66"]

export function OrbitRings({
  count = 3,
  baseRadius = 5,
  gap = 2,
  colors = DEFAULT_COLORS,
  speed = 0.15,
}: OrbitRingsProps) {
  const group = useRef<THREE.Group>(null)

  useFrame((state) => {
    if (!group.current) return
    group.current.children.forEach((ring, i) => {
      ring.rotation.z = state.clock.elapsedTime * speed * (i + 1)
    })
  })

  return (
    <group ref={group}>
      {Array.from({ length: count }).map((_, i) => (
        <mesh key={i} rotation={[Math.PI / 2, i * 0.5, 0]}>
          <torusGeometry args={[baseRadius + i * gap, 0.04, 16, 120]} />
          <meshBasicMaterial
            color={colors[i % colors.length]}
            transparent
            opacity={0.35}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  )
}
