import type * as React from "react"
import type * as Three from "three"

declare module "@react-three/fiber" {
  export const Canvas: React.FC<{
    children?: React.ReactNode
    camera?: Three.Camera | { position?: [number, number, number]; fov?: number; near?: number; far?: number }
    dpr?: number | [number, number]
    gl?: { antialias?: boolean; alpha?: boolean; powerPreference?: "high-performance" | "low-power" | "default" }
    style?: React.CSSProperties
    onCreated?: (state: { gl: Three.WebGLRenderer; scene: Three.Scene; camera: Three.Camera }) => void
    onPointerMissed?: (event: React.PointerEvent) => void
    events?: { priority?: number; compute?: (event: React.PointerEvent) => Ray[] }
    raycast?: (event: React.PointerEvent, camera: Three.Camera, objects: Three.Object3D[]) => Three.Intersection[]
    shadows?: boolean | { type?: Three.ShadowMapType }
    linear?: boolean
    flat?: boolean
    legacy?: boolean
    performance?: { min?: number; max?: number; regress?: number }
    [key: string]: unknown
  }>
  
  export function useThree(): {
    gl: Three.WebGLRenderer
    scene: Three.Scene
    camera: Three.Camera
    raycaster: Three.Raycaster
    mouse: Three.Vector2
    size: { width: number; height: number }
    viewport: { width: number; height: number; factor: number }
    clock: Three.Clock
    raycaster: Three.Raycaster
    set: (props: Record<string, unknown>) => void
    setSize: (width: number, height: number) => void
    setCamera: (camera: Three.Camera) => void
    invalidate: (frames?: number) => void
    advance: (timestamp: number, runGlobalEffects?: boolean) => void
  }
  
  export function useFrame(callback: (state: ReturnType<typeof useThree>, delta: number) => void, renderPriority?: number): void
  
  export function extend(objects: Record<string, React.ComponentType<unknown>>): void
  
  export function createPortal(children: React.ReactNode, container: Three.Object3D): React.ReactPortal
  
  export const a: React.ReactElement<unknown>
  export const group: React.ReactElement<unknown>
  export const mesh: React.ReactElement<unknown>
  export const primitive: React.ReactElement<unknown>
}

declare module "react" {
  namespace JSX {
    interface IntrinsicElements {
      ambientLight: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        intensity?: number
        color?: Three.ColorRepresentation
        [key: string]: unknown
      }
      pointLight: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        intensity?: number
        color?: Three.ColorRepresentation
        position?: [number, number, number]
        distance?: number
        decay?: number
        [key: string]: unknown
      }
      directionalLight: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        intensity?: number
        color?: Three.ColorRepresentation
        position?: [number, number, number]
        target?: Three.Object3D
        [key: string]: unknown
      }
      spotLight: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        intensity?: number
        color?: Three.ColorRepresentation
        position?: [number, number, number]
        target?: Three.Object3D
        angle?: number
        penumbra?: number
        decay?: number
        distance?: number
        [key: string]: unknown
      }
      hemisphereLight: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        intensity?: number
        color?: Three.ColorRepresentation
        groundColor?: Three.ColorRepresentation
        position?: [number, number, number]
        [key: string]: unknown
      }
      rectAreaLight: React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement>, HTMLElement> & {
        intensity?: number
        color?: Three.ColorRepresentation
        position?: [number, number, number]
        width?: number
        height?: number
        [key: string]: unknown
      }
    }
  }
}