import { useRef } from "react"
import { useFrame } from "@react-three/fiber"
import * as THREE from "three"
import type { CoreOrbProps } from "../types"

export function CoreOrb({
  radius = 3,
  color = "#00f0ff",
  emissiveIntensity = 0.5,
}: CoreOrbProps) {
  const mesh = useRef<THREE.Mesh>(null)
  const mat = useRef<THREE.MeshPhysicalMaterial>(null)

  useFrame((state) => {
    if (!mesh.current) return
    mesh.current.rotation.x = state.clock.elapsedTime * 0.2
    mesh.current.rotation.y = state.clock.elapsedTime * 0.3
    const s = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.08
    mesh.current.scale.setScalar(s)
  })

  return (
    <mesh ref={mesh}>
      <icosahedronGeometry args={[radius, 3]} />
      <meshPhysicalMaterial
        ref={mat}
        color={color}
        metalness={0.3}
        roughness={0.2}
        transmission={0.5}
        thickness={1}
        clearcoat={1}
        clearcoatRoughness={0.1}
        emissive={color}
        emissiveIntensity={emissiveIntensity}
      />
    </mesh>
  )
}
