import { useMemo, useRef } from "react"
import { useFrame } from "@react-three/fiber"
import * as THREE from "three"
import type { NeuralParticlesProps } from "../types"

const vertexShader = /* glsl */ `
  attribute float size;
  attribute vec3 customColor;
  varying vec3 vColor;
  uniform float uTime;
  uniform vec3 uMouse;
  uniform float uRepulsionRadius;
  uniform float uRepulsionStrength;

  void main() {
    vColor = customColor;
    vec3 pos = position;

    // gentle drift
    pos.x += sin(uTime * 0.3 + position.y * 0.2) * 0.15;
    pos.y += cos(uTime * 0.25 + position.z * 0.2) * 0.15;

    // mouse repulsion
    vec3 toMouse = pos - uMouse;
    float dist = length(toMouse);
    if (dist < uRepulsionRadius && dist > 0.001) {
      float force = uRepulsionStrength / (dist * dist);
      pos += normalize(toMouse) * min(force, uRepulsionStrength);
    }

    vec4 mv = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mv;
    gl_PointSize = size * (120.0 / -mv.z);
  }
`

const fragmentShader = /* glsl */ `
  varying vec3 vColor;
  void main() {
    float d = length(gl_PointCoord - vec2(0.5));
    if (d > 0.5) discard;
    float alpha = 1.0 - smoothstep(0.0, 0.5, d);
    gl_FragColor = vec4(vColor, alpha * 0.85);
  }
`

export function NeuralParticles({
  count = 12000,
  radius = 22,
  colorA = "#00f0ff",
  colorB = "#e024c3",
  repulsionStrength = 0.6,
  repulsionRadius = 8,
  mouse = null,
}: NeuralParticlesProps) {
  const points = useRef<THREE.Points>(null)
  const matRef = useRef<THREE.ShaderMaterial>(null)

  const { positions, colors, sizes } = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const sizes = new Float32Array(count)
    const cA = new THREE.Color(colorA)
    const cB = new THREE.Color(colorB)
    for (let i = 0; i < count; i++) {
      const r = 4 + Math.random() * radius
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = r * Math.cos(phi)
      const c = cA.clone().lerp(cB, Math.random())
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
      sizes[i] = 0.4 + Math.random() * 1.4
    }
    return { positions, colors, sizes }
  }, [count, radius, colorA, colorB])

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uMouse: { value: new THREE.Vector3(0, 0, 0) },
      uRepulsionRadius: { value: repulsionRadius },
      uRepulsionStrength: { value: repulsionStrength },
    }),
    [repulsionRadius, repulsionStrength]
  )

  useFrame((state) => {
    if (!matRef.current) return
    matRef.current.uniforms.uTime.value = state.clock.elapsedTime
    if (mouse) {
      const vec = new THREE.Vector3(mouse.x, mouse.y, 0.5).unproject(state.camera)
      const dir = vec.sub(state.camera.position).normalize()
      const dist = -state.camera.position.z / dir.z
      const world = state.camera.position.clone().add(dir.multiplyScalar(dist))
      matRef.current.uniforms.uMouse.value.lerp(world, 0.1)
    }
  })

  const geometry = useMemo(() => {
    const g = new THREE.BufferGeometry()
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3))
    g.setAttribute("customColor", new THREE.BufferAttribute(colors, 3))
    g.setAttribute("size", new THREE.BufferAttribute(sizes, 1))
    return g
  }, [positions, colors, sizes])

  return (
    <points ref={points} geometry={geometry} frustumCulled={false}>
      <shaderMaterial
        ref={matRef}
        vertexShader={vertexShader}
        fragmentShader={fragmentShader}
        uniforms={uniforms}
        transparent
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </points>
  )
}
