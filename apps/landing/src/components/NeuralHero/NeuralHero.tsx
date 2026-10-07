'use client'

import { useRef, useEffect, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export function NeuralHero() {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('high')

  useEffect(() => {
    if (!containerRef.current || !canvasRef.current) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.set(0, 0, 50)

    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current!,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setClearColor(0x01050e, 1)

    // Particles
    const geometry = new THREE.BufferGeometry()
    const count = 15000
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const sizes = new Float32Array(count)

    for (let i = 0; i < count; i++) {
      const radius = 5 + Math.random() * 20
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i * 3 + 2] = radius * Math.cos(phi)

      const color = new THREE.Color()
      color.setHSL(0.5 + (positions[i * 3] / 50) * 0.3, 1, 0.5)
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b

      sizes[i] = 0.5 + Math.random() * 1.5
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

    const material = new THREE.PointsMaterial({
      size: 1,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending,
      sizeAttenuation: true,
    })

    const particles = new THREE.Points(geometry, material)
    scene.add(particles)

    // Central orb
    const orbGeometry = new THREE.IcosahedronGeometry(3, 3)
    const orbMaterial = new THREE.MeshPhysicalMaterial({
      color: 0x00f0ff,
      metalness: 0.3,
      roughness: 0.2,
      transmission: 0.5,
      clearcoat: 1,
      emissive: 0x00f0ff,
      emissiveIntensity: 0.5,
    })
    const orb = new THREE.Mesh(orbGeometry, orbMaterial)
    scene.add(orb)

    // Rings
    const rings = []
    for (let i = 0; i < 3; i++) {
      const ringGeometry = new THREE.TorusGeometry(5 + i * 2, 0.05, 16, 100)
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: i === 0 ? 0x00f0ff : i === 1 ? 0xe024c3 : 0x00ff66,
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide,
      })
      const ring = new THREE.Mesh(ringGeometry, ringMaterial)
      ring.rotation.x = Math.PI / 2
      ring.rotation.y = i * 0.5
      scene.add(ring)
      rings.push(ring)
    }

    // Lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5)
    scene.add(ambientLight)
    const pointLight = new THREE.PointLight(0x00f0ff, 1, 100)
    pointLight.position.set(10, 10, 10)
    scene.add(pointLight)

    // Stars
    const starGeometry = new THREE.BufferGeometry()
    const starPositions = new Float32Array(2000 * 3)
    for (let i = 0; i < 2000; i++) {
      const radius = 80 + Math.random() * 40
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      starPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta)
      starPositions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      starPositions[i * 3 + 2] = radius * Math.cos(phi)
    }
    starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3))
    const starMaterial = new THREE.PointsMaterial({ color: 0xffffff, size: 0.5, transparent: true, opacity: 0.6 })
    const stars = new THREE.Points(starGeometry, starMaterial)
    scene.add(stars)

    // Controls
    const controls = new OrbitControls(camera, canvasRef.current!)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.2

    // Animation
    let time = 0
    const animate = () => {
      requestAnimationFrame(animate)
      time += 0.01

      orb.rotation.x += 0.002
      orb.rotation.y += 0.003
      const scale = 1 + Math.sin(time * 2) * 0.1
      orb.scale.setScalar(scale)

      rings.forEach((ring, i) => {
        ring.rotation.z += 0.001 * (i + 1)
      })

      camera.position.x = Math.sin(time * 0.1) * 3
      camera.position.y = Math.cos(time * 0.07) * 2
      camera.lookAt(0, 0, 0)

      controls.update()
      renderer.render(scene, camera)
    }

    animate()

    // Resize
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <div ref={containerRef} className="fixed inset-0 -z-10" style={{ touchAction: 'none' }}>
      <canvas ref={canvasRef} className="w-full h-full" />
      
      <div className="fixed inset-0 z-10 flex flex-col items-center justify-center px-6">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-900/80 backdrop-blur-xl border border-cyan-500/30 mb-8">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
            <span className="text-xs font-mono text-cyan-400 tracking-wider">LIVE NEURAL CORE</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-display font-light tracking-tight leading-[1.1] mb-6">
            Orchestrate <span className="text-cyan-400">19 AI engines.</span><br/>
            Zero cloud cost.<br/>
            <span className="text-magenta-400">Your infrastructure.</span>
          </h1>
          
          <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10">
            Daniela — your personal AI, renamed by you. Runs on phone, desktop, server. Voice, vision, code, control.
          </p>
          
          <div className="flex flex-wrap gap-4 justify-center mb-16">
            <a href="/shell" className="btn-primary">Enter Neural Shell</a>
            <a href="#demo" className="btn-secondary">Watch Demo</a>
            <a href="#download" className="btn-ghost">Download APK</a>
          </div>
          
          <div className="flex items-center gap-8 justify-center text-sm text-gray-500">
            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-green-400"></span> MIT License</div>
            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-cyan-400"></span> FIPS 140-3 L3</div>
            <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-magenta-400"></span> Android + Windows</div>
          </div>
        </div>
      </div>

      <div className="fixed bottom-8 right-8 md:static md:absolute md:bottom-20 md:right-10 z-20">
        <div className="glass-strong rounded-xl p-4 text-center">
          <p className="text-xs text-gray-500 mb-2">Get the App</p>
          <div id="qr-apk" className="mx-auto"></div>
          <p className="text-xs text-gray-500 mt-2">Scan → Install APK</p>
        </div>
      </div>
    </>
  )
}
