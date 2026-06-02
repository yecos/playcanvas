'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import * as pc from 'playcanvas'
import { Hud } from './Hud'
import { StartScreen } from './StartScreen'
import { GameOverScreen } from './GameOverScreen'
import { Joystick } from './Joystick'

interface GameState {
  score: number
  timeLeft: number
  isPlaying: boolean
  isGameOver: boolean
  crystalsCollected: number
  totalCrystals: number
}

// ---- MATERIAL HELPERS ----

function createPlayerMaterial(): pc.StandardMaterial {
  const material = new pc.StandardMaterial()
  material.diffuse = new pc.Color(1, 0.5, 0.1)
  material.emissive = new pc.Color(1, 0.3, 0)
  material.emissiveIntensity = 2
  material.metalness = 0.7
  material.gloss = 0.8
  material.update()
  return material
}

function createGroundMaterial(): pc.StandardMaterial {
  const material = new pc.StandardMaterial()
  material.diffuse = new pc.Color(0.15, 0.18, 0.25)
  material.emissive = new pc.Color(0.02, 0.03, 0.06)
  material.metalness = 0.3
  material.gloss = 0.5
  material.update()
  return material
}

function createGridLineMaterial(): pc.StandardMaterial {
  const material = new pc.StandardMaterial()
  material.diffuse = new pc.Color(0.2, 0.3, 0.5)
  material.emissive = new pc.Color(0.1, 0.15, 0.3)
  material.emissiveIntensity = 0.5
  material.update()
  return material
}

function createPillarMaterial(): pc.StandardMaterial {
  const material = new pc.StandardMaterial()
  material.diffuse = new pc.Color(0.25, 0.2, 0.35)
  material.emissive = new pc.Color(0.05, 0.02, 0.1)
  material.metalness = 0.6
  material.gloss = 0.7
  material.update()
  return material
}

function createGlowMaterial(color: pc.Color): pc.StandardMaterial {
  const material = new pc.StandardMaterial()
  material.diffuse = color
  material.emissive = color
  material.emissiveIntensity = 3
  material.metalness = 0.5
  material.gloss = 1
  material.update()
  return material
}

const CRYSTAL_POSITIONS = [
  { x: 5, z: 5 }, { x: -5, z: 5 }, { x: 5, z: -5 }, { x: -5, z: -5 },
  { x: 10, z: 0 }, { x: -10, z: 0 }, { x: 0, z: 10 }, { x: 0, z: -10 },
  { x: 7, z: 7 }, { x: -7, z: 7 }, { x: 7, z: -7 }, { x: -7, z: -7 },
  { x: 3, z: 12 }, { x: -3, z: -12 }, { x: 12, z: 3 }, { x: -12, z: -3 },
  { x: 15, z: 0 }, { x: -15, z: 0 }, { x: 0, z: 15 }, { x: 0, z: -15 },
]

const CRYSTAL_COLORS = [
  new pc.Color(1, 0.2, 0.5),
  new pc.Color(0.2, 0.5, 1),
  new pc.Color(0.2, 1, 0.5),
]

export function GameCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const appRef = useRef<pc.Application | null>(null)
  const playerRef = useRef<pc.Entity | null>(null)
  const cameraRef = useRef<pc.Entity | null>(null)
  const crystalsRef = useRef<pc.Entity[]>([])
  const particlesRef = useRef<{ entity: pc.Entity; velocity: pc.Vec3; life: number }[]>([])
  const joystickInputRef = useRef({ x: 0, y: 0 })
  const gameStateRef = useRef<GameState>({
    score: 0,
    timeLeft: 60,
    isPlaying: false,
    isGameOver: false,
    crystalsCollected: 0,
    totalCrystals: CRYSTAL_POSITIONS.length,
  })
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [gameState, setGameState] = useState<GameState>({
    score: 0,
    timeLeft: 60,
    isPlaying: false,
    isGameOver: false,
    crystalsCollected: 0,
    totalCrystals: CRYSTAL_POSITIONS.length,
  })

  const [isLoaded, setIsLoaded] = useState(false)

  const handleJoystick = useCallback((x: number, y: number) => {
    joystickInputRef.current = { x, y }
  }, [])

  const spawnParticles = useCallback((position: pc.Vec3, color: pc.Color) => {
    const app = appRef.current
    if (!app) return

    for (let i = 0; i < 8; i++) {
      const particle = new pc.Entity()
      particle.addComponent('render', {
        type: 'sphere',
        material: createGlowMaterial(color),
      })
      particle.setPosition(position.x, position.y, position.z)
      particle.setLocalScale(0.15, 0.15, 0.15)
      app.root.addChild(particle)

      const velocity = new pc.Vec3(
        (Math.random() - 0.5) * 4,
        Math.random() * 3 + 1,
        (Math.random() - 0.5) * 4
      )
      particlesRef.current.push({ entity: particle, velocity, life: 1.0 })
    }
  }, [])

  const respawnCrystals = useCallback(() => {
    const app = appRef.current
    if (!app) return

    // Remove existing crystals
    crystalsRef.current.forEach(c => {
      if (c.parent) c.parent.removeChild(c)
      c.destroy()
    })
    crystalsRef.current = []

    CRYSTAL_POSITIONS.forEach((pos, i) => {
      const crystal = new pc.Entity(`crystal_${i}`)
      crystal.addComponent('render', {
        type: 'box',
        material: createGlowMaterial(CRYSTAL_COLORS[i % 3]),
      })
      crystal.setPosition(pos.x, 1.0, pos.z)
      crystal.setLocalScale(0.5, 0.8, 0.5)
      app.root.addChild(crystal)
      crystalsRef.current.push(crystal)
    })
  }, [])

  const startGame = useCallback(() => {
    const gs = gameStateRef.current
    gs.score = 0
    gs.timeLeft = 60
    gs.isPlaying = true
    gs.isGameOver = false
    gs.crystalsCollected = 0
    setGameState({ ...gs })

    // Reset player position
    if (playerRef.current?.rigidbody) {
      playerRef.current.rigidbody.teleport(0, 0.6, 0)
    }

    // Respawn crystals
    respawnCrystals()

    // Start timer
    if (timerRef.current) clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      const g = gameStateRef.current
      if (!g.isPlaying) return
      g.timeLeft--
      setGameState({ ...g })
      if (g.timeLeft <= 0) {
        g.isPlaying = false
        g.isGameOver = true
        setGameState({ ...g })
        if (timerRef.current) clearInterval(timerRef.current)
      }
    }, 1000)
  }, [respawnCrystals])

  const restartGame = useCallback(() => {
    startGame()
  }, [startGame])

  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const app = new pc.Application(canvas, {
      mouse: new pc.Mouse(canvas),
      touch: new pc.TouchDevice(canvas),
    })
    appRef.current = app

    app.setCanvasFillMode(pc.FILLMODE_FILL_WINDOW)
    app.setCanvasResolution(pc.RESOLUTION_AUTO)

    // Enable shadows
    app.scene.shadowMapType = pc.SHADOW_PCF3

    // Set ambient light
    app.scene.ambientLight = new pc.Color(0.3, 0.3, 0.4)

    // ---- LIGHTS ----
    const light = new pc.Entity('sun')
    light.addComponent('light', {
      type: 'directional',
      color: new pc.Color(1, 0.95, 0.8),
      intensity: 1.5,
      castShadows: true,
      shadowResolution: 1024,
      shadowDistance: 30,
      shadowBias: 0.2,
      normalOffsetBias: 0.05,
    })
    light.setLocalEulerAngles(45, 30, 0)
    app.root.addChild(light)

    const ambientLightEntity = new pc.Entity('ambient')
    ambientLightEntity.addComponent('light', {
      type: 'point',
      color: new pc.Color(0.4, 0.4, 0.6),
      intensity: 0.5,
      range: 50,
    })
    ambientLightEntity.setPosition(0, 10, 0)
    app.root.addChild(ambientLightEntity)

    // ---- GROUND ----
    const ground = new pc.Entity('ground')
    ground.addComponent('render', {
      type: 'box',
      material: createGroundMaterial(),
    })
    ground.setPosition(0, -0.25, 0)
    ground.setLocalScale(40, 0.5, 40)
    app.root.addChild(ground)

    // Grid lines on ground
    for (let i = -18; i <= 18; i += 6) {
      const lineH = new pc.Entity(`gridH_${i}`)
      lineH.addComponent('render', { type: 'box', material: createGridLineMaterial() })
      lineH.setPosition(i, 0.02, 0)
      lineH.setLocalScale(0.05, 0.02, 40)
      app.root.addChild(lineH)

      const lineV = new pc.Entity(`gridV_${i}`)
      lineV.addComponent('render', { type: 'box', material: createGridLineMaterial() })
      lineV.setPosition(0, 0.02, i)
      lineV.setLocalScale(40, 0.02, 0.05)
      app.root.addChild(lineV)
    }

    // Decorative pillars
    const pillarPositions = [
      { x: 8, z: 8 }, { x: -8, z: 8 }, { x: 8, z: -8 }, { x: -8, z: -8 },
      { x: 16, z: 16 }, { x: -16, z: 16 }, { x: 16, z: -16 }, { x: -16, z: -16 },
    ]
    pillarPositions.forEach((p, i) => {
      const pillar = new pc.Entity(`pillar_${i}`)
      pillar.addComponent('render', { type: 'cylinder', material: createPillarMaterial() })
      pillar.setPosition(p.x, 1.5, p.z)
      pillar.setLocalScale(0.6, 3, 0.6)
      app.root.addChild(pillar)
    })

    // ---- PLAYER ----
    const player = new pc.Entity('player')
    player.addComponent('render', {
      type: 'sphere',
      material: createPlayerMaterial(),
    })
    player.setPosition(0, 0.6, 0)
    player.setLocalScale(1, 1, 1)
    app.root.addChild(player)
    playerRef.current = player

    // Player glow light
    const playerLight = new pc.Entity('playerLight')
    playerLight.addComponent('light', {
      type: 'point',
      color: new pc.Color(1, 0.6, 0.2),
      intensity: 2,
      range: 8,
    })
    playerLight.setPosition(0, 1, 0)
    player.addChild(playerLight)

    // ---- CAMERA ----
    const camera = new pc.Entity('camera')
    camera.addComponent('camera', {
      clearColor: new pc.Color(0.05, 0.05, 0.12),
      fov: 60,
      nearClip: 0.1,
      farClip: 100,
    })
    camera.setPosition(0, 14, 14)
    camera.setLocalEulerAngles(-45, 0, 0)
    app.root.addChild(camera)
    cameraRef.current = camera

    // ---- CRYSTALS ----
    respawnCrystals()

    // ---- GAME LOOP ----
    let lastTime = 0
    const playerSpeed = 8

    app.on('update', (dt: number) => {
      const gs = gameStateRef.current
      if (!gs.isPlaying || !playerRef.current) return

      lastTime += dt

      // Apply joystick input as position change
      const input = joystickInputRef.current
      const currentPos = player.getPosition()

      const newX = currentPos.x + input.x * playerSpeed * dt
      const newZ = currentPos.z - input.y * playerSpeed * dt

      // Clamp to arena bounds
      const clampedX = Math.max(-18, Math.min(18, newX))
      const clampedZ = Math.max(-18, Math.min(18, newZ))

      player.setPosition(clampedX, 0.6, clampedZ)

      // Camera follows player smoothly
      const camTarget = new pc.Vec3(clampedX, 14, clampedZ + 14)
      const camPos = camera.getPosition()
      camPos.lerp(camPos, camTarget, 0.05)
      camera.setPosition(camPos)

      // Check crystal collisions
      const playerPos = player.getPosition()
      const crystalsToRemove: pc.Entity[] = []

      crystalsRef.current.forEach((crystal) => {
        if (!crystal.parent) return

        // Rotate crystals
        const rot = crystal.getLocalEulerAngles()
        crystal.setLocalEulerAngles(rot.x, rot.y + 90 * dt, rot.z + 45 * dt)

        // Bob up and down
        const crystalPos = crystal.getPosition()
        crystal.setPosition(crystalPos.x, 1.0 + Math.sin(lastTime * 3 + crystalPos.x) * 0.3, crystalPos.z)

        // Check distance to player
        const dist = playerPos.distance(crystalPos)
        if (dist < 1.5) {
          crystalsToRemove.push(crystal)
          gs.score += 10
          gs.crystalsCollected++
          setGameState({ ...gs })
        }
      })

      // Remove collected crystals with particles
      crystalsToRemove.forEach(crystal => {
        spawnParticles(crystal.getPosition(), new pc.Color(1, 0.8, 0.2))
        if (crystal.parent) crystal.parent.removeChild(crystal)
        crystal.destroy()
        crystalsRef.current = crystalsRef.current.filter(c => c !== crystal)
      })

      // Check win condition
      if (crystalsRef.current.length === 0) {
        gs.score += gs.timeLeft * 5 // Bonus for remaining time
        gs.isPlaying = false
        gs.isGameOver = true
        setGameState({ ...gs })
        if (timerRef.current) clearInterval(timerRef.current)
      }

      // Update particles
      const particlesToRemove: number[] = []
      particlesRef.current.forEach((p, i) => {
        p.life -= dt * 2
        if (p.life <= 0) {
          particlesToRemove.push(i)
          if (p.entity.parent) p.entity.parent.removeChild(p.entity)
          p.entity.destroy()
        } else {
          const pPos = p.entity.getPosition()
          p.entity.setPosition(
            pPos.x + p.velocity.x * dt,
            pPos.y + p.velocity.y * dt,
            pPos.z + p.velocity.z * dt
          )
          p.velocity.y -= 9.8 * dt
          const scale = p.life * 0.15
          p.entity.setLocalScale(scale, scale, scale)
        }
      })
      particlesToRemove.reverse().forEach(i => {
        particlesRef.current.splice(i, 1)
      })

      // Player pulse animation
      const pulseScale = 1 + Math.sin(lastTime * 4) * 0.05
      player.setLocalScale(pulseScale, pulseScale, pulseScale)
    })

    app.start()
    setIsLoaded(true)

    return () => {
      app.destroy()
      appRef.current = null
      if (timerRef.current) clearInterval(timerRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const allCrystalsCollected = gameState.isGameOver && gameState.crystalsCollected === gameState.totalCrystals && gameState.timeLeft > 0

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-black">
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full"
        style={{ touchAction: 'none' }}
      />

      {/* HUD */}
      {gameState.isPlaying && (
        <Hud
          score={gameState.score}
          timeLeft={gameState.timeLeft}
          crystalsCollected={gameState.crystalsCollected}
          totalCrystals={gameState.totalCrystals}
        />
      )}

      {/* Joystick */}
      {gameState.isPlaying && (
        <Joystick onMove={handleJoystick} />
      )}

      {/* Start Screen */}
      {!gameState.isPlaying && !gameState.isGameOver && isLoaded && (
        <StartScreen onStart={startGame} />
      )}

      {/* Game Over Screen */}
      {gameState.isGameOver && (
        <GameOverScreen
          score={gameState.score}
          crystalsCollected={gameState.crystalsCollected}
          totalCrystals={gameState.totalCrystals}
          won={allCrystalsCollected}
          onRestart={restartGame}
        />
      )}

      {/* Loading */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 z-50">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-orange-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white text-lg font-medium">Cargando...</p>
          </div>
        </div>
      )}
    </div>
  )
}
