'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import * as pc from 'playcanvas'
import { Hud } from './Hud'
import { StartScreen } from './StartScreen'
import { GameOverScreen } from './GameOverScreen'
import { Joystick } from './Joystick'
import { ModelSelector } from './ModelSelector'

interface GameState {
  score: number
  timeLeft: number
  isPlaying: boolean
  isGameOver: boolean
  crystalsCollected: number
  totalCrystals: number
}

// ---- MATERIAL HELPERS ----

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

function createSphereMaterial(): pc.StandardMaterial {
  const mat = new pc.StandardMaterial()
  mat.diffuse = new pc.Color(1, 0.5, 0.1)
  mat.emissive = new pc.Color(1, 0.3, 0)
  mat.emissiveIntensity = 2
  mat.metalness = 0.7
  mat.gloss = 0.8
  mat.update()
  return mat
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

// Available character models
const CHARACTER_MODELS = [
  {
    id: 'fox',
    name: 'Zorro',
    icon: '🦊',
    url: '/models/fox.glb',
    scale: 5.0,
    yOffset: 0.5,
    description: 'Zorro animado con 3 animaciones',
  },
  {
    id: 'robot',
    name: 'Robot',
    icon: '🤖',
    url: '/models/brainstem.glb',
    scale: 5.0,
    yOffset: 0.5,
    description: 'Robot BrainStem con animaciones',
  },
  {
    id: 'sphere',
    name: 'Esfera',
    icon: '🔮',
    url: null,
    scale: 1,
    yOffset: 0.6,
    description: 'Esfera brillante (sin modelo)',
  },
]

export function GameCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const appRef = useRef<pc.Application | null>(null)
  const playerRef = useRef<pc.Entity | null>(null)
  const playerModelRef = useRef<pc.Entity | null>(null)
  const cameraRef = useRef<pc.Entity | null>(null)
  const crystalsRef = useRef<pc.Entity[]>([])
  const particlesRef = useRef<{ entity: pc.Entity; velocity: pc.Vec3; life: number }[]>([])
  const joystickInputRef = useRef({ x: 0, y: 0 })
  const currentAnimRef = useRef<string>('')
  const gameStateRef = useRef<GameState>({
    score: 0,
    timeLeft: 60,
    isPlaying: false,
    isGameOver: false,
    crystalsCollected: 0,
    totalCrystals: CRYSTAL_POSITIONS.length,
  })
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const selectedModelRef = useRef<string>('fox')

  const [gameState, setGameState] = useState<GameState>({
    score: 0,
    timeLeft: 60,
    isPlaying: false,
    isGameOver: false,
    crystalsCollected: 0,
    totalCrystals: CRYSTAL_POSITIONS.length,
  })

  const [isLoaded, setIsLoaded] = useState(false)
  const [selectedModel, setSelectedModel] = useState('fox')
  const [modelLoading, setModelLoading] = useState(false)

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

  // Play an animation on the player model
  const playAnimation = useCallback((animName: string) => {
    const playerModel = playerModelRef.current
    if (!playerModel?.anim) return
    if (currentAnimRef.current === animName) return

    try {
      if (playerModel.anim.baseLayer) {
        playerModel.anim.baseLayer.transition(animName, 0.2)
        currentAnimRef.current = animName
      }
    } catch {
      // Animation might not exist
    }
  }, [])

  // Load a GLB model and replace the current player model
  const loadModel = useCallback((modelConfig: typeof CHARACTER_MODELS[0]) => {
    const app = appRef.current
    const player = playerRef.current
    if (!app || !player) return

    setModelLoading(true)

    // Remove previous model
    if (playerModelRef.current) {
      player.removeChild(playerModelRef.current)
      playerModelRef.current.destroy()
      playerModelRef.current = null
    }

    if (!modelConfig.url) {
      // Sphere mode
      const sphereEntity = new pc.Entity('playerModel')
      sphereEntity.addComponent('render', {
        type: 'sphere',
        material: createSphereMaterial(),
      })
      sphereEntity.setLocalScale(modelConfig.scale, modelConfig.scale, modelConfig.scale)
      sphereEntity.setPosition(0, modelConfig.yOffset, 0)
      player.addChild(sphereEntity)
      playerModelRef.current = sphereEntity

      const glowLight = new pc.Entity('glowLight')
      glowLight.addComponent('light', {
        type: 'point',
        color: new pc.Color(1, 0.6, 0.2),
        intensity: 2,
        range: 8,
      })
      glowLight.setPosition(0, 0.5, 0)
      sphereEntity.addChild(glowLight)

      setModelLoading(false)
      return
    }

    // Load GLB model
    const containerAsset = new pc.Asset(modelConfig.id, 'container', {
      url: modelConfig.url,
    })

    containerAsset.on('load', () => {
      const resource = containerAsset.resource
      console.log('[DEBUG] Model loaded:', modelConfig.id, 'animations:', resource.animations?.length || 0)

      let modelEntity: pc.Entity
      try {
        modelEntity = resource.instantiateRenderEntity({
          castShadows: true,
        })
        console.log('[DEBUG] Entity instantiated, name:', modelEntity.name, 'children:', modelEntity.children.length)

        // Debug: check render components
        const checkRender = (entity: pc.Entity, depth = 0) => {
          const render = entity.render
          console.log('[DEBUG]', '  '.repeat(depth), entity.name, 'render:', !!render, 'type:', render?.type, 'meshes:', render?.meshInstances?.length || 0)
          entity.children.forEach((child: pc.Entity) => checkRender(child, depth + 1))
        }
        checkRender(modelEntity)
      } catch (e) {
        console.error('Failed to instantiate model entity:', e)
        // Fallback to sphere
        const sphereEntity = new pc.Entity('playerModel_fallback')
        sphereEntity.addComponent('render', {
          type: 'sphere',
          material: createSphereMaterial(),
        })
        sphereEntity.setLocalScale(1, 1, 1)
        sphereEntity.setPosition(0, 0.6, 0)
        player.addChild(sphereEntity)
        playerModelRef.current = sphereEntity
        setModelLoading(false)
        return
      }

      modelEntity.setLocalScale(modelConfig.scale, modelConfig.scale, modelConfig.scale)
      modelEntity.setPosition(0, modelConfig.yOffset, 0)
      modelEntity.name = 'playerModel'
      console.log('[DEBUG] Entity configured, scale:', modelConfig.scale, 'yOffset:', modelConfig.yOffset)

      // Add entity to scene
      player.addChild(modelEntity)
      playerModelRef.current = modelEntity
      console.log('[DEBUG] Entity added to player, player children:', player.children.length)

      // Debug: add a reference cube directly to the scene root
      try {
        const debugCube = new pc.Entity('debugCube')
        debugCube.addComponent('render', {
          type: 'box',
          material: createGlowMaterial(new pc.Color(0, 1, 0)),
        })
        debugCube.setPosition(0, 3, 0)
        debugCube.setLocalScale(2, 2, 2)
        player.addChild(debugCube)  // Add as child of player so it follows
        console.log('[DEBUG] Green debug cube added as child of player at (0, 3, 0)')
      } catch (e) {
        console.warn('[DEBUG] Failed to add debug cube:', e)
      }

      // Setup animations if available (errors here should NOT replace the model with a sphere)
      if (resource.animations && resource.animations.length > 0) {
        try {
          modelEntity.addComponent('anim')

          // Build a state graph from the available animations
          const stateNames: string[] = []
          const animMap = new Map<string, pc.Asset>()

          resource.animations.forEach((animAsset: pc.Asset, idx: number) => {
            const rawName = animAsset.name || `anim_${idx}`
            let stateName = rawName
            const lower = rawName.toLowerCase()
            if (lower.includes('survey') || lower.includes('idle')) {
              stateName = 'idle'
            } else if (lower.includes('walk')) {
              stateName = 'walk'
            } else if (lower.includes('run')) {
              stateName = 'run'
            }
            stateNames.push(stateName)
            animMap.set(stateName, animAsset)
          })

          // Create a state graph with transitions between idle/walk/run
          const states = stateNames.map(s => ({ name: s }))
          const transitions = stateNames.flatMap(from =>
            stateNames
              .filter(to => to !== from)
              .map(to => ({
                from: from,
                to: to,
                time: 0.2,
                priority: 1,
              }))
          )

          modelEntity.anim.loadStateGraph({
            layers: [{
              name: 'base',
              states: states,
              transitions: transitions,
            }],
            parameters: {},
          })

          const layer = modelEntity.anim.baseLayer

          // Assign animation tracks to states
          animMap.forEach((animAsset, stateName) => {
            const track = animAsset.resource
            layer.assignAnimation(stateName, track)
          })

          // Start with idle
          try { layer.transition('idle', 0) } catch { /* no idle anim */ }
          currentAnimRef.current = 'idle'
        } catch (e) {
          console.warn('Animation setup warning (model still visible):', e)
        }
      }

      setModelLoading(false)
    })

    containerAsset.on('error', (err: string) => {
      console.error('Failed to load model:', err)
      // Fallback to sphere
      const sphereEntity = new pc.Entity('playerModel_fallback')
      sphereEntity.addComponent('render', {
        type: 'sphere',
        material: createSphereMaterial(),
      })
      sphereEntity.setLocalScale(1, 1, 1)
      sphereEntity.setPosition(0, 0.6, 0)
      player.addChild(sphereEntity)
      playerModelRef.current = sphereEntity
      setModelLoading(false)
    })

    app.assets.add(containerAsset)
    app.assets.load(containerAsset)
  }, [])

  const handleModelChange = useCallback((modelId: string) => {
    selectedModelRef.current = modelId
    setSelectedModel(modelId)

    const modelConfig = CHARACTER_MODELS.find(m => m.id === modelId)
    if (modelConfig) {
      loadModel(modelConfig)
    }
  }, [loadModel])

  const startGame = useCallback(() => {
    const gs = gameStateRef.current
    gs.score = 0
    gs.timeLeft = 60
    gs.isPlaying = true
    gs.isGameOver = false
    gs.crystalsCollected = 0
    setGameState({ ...gs })

    if (playerRef.current) {
      playerRef.current.setPosition(0, 0, 0)
    }

    respawnCrystals()
    playAnimation('idle')

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
  }, [respawnCrystals, playAnimation])

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
    app.scene.shadowMapType = pc.SHADOW_PCF3
    app.scene.ambientLight = new pc.Color(0.4, 0.4, 0.5)

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
    ground.addComponent('render', { type: 'box', material: createGroundMaterial() })
    ground.setPosition(0, -0.25, 0)
    ground.setLocalScale(40, 0.5, 40)
    app.root.addChild(ground)

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
    player.setPosition(0, 0, 0)
    app.root.addChild(player)
    playerRef.current = player

    const playerLight = new pc.Entity('playerLight')
    playerLight.addComponent('light', {
      type: 'point',
      color: new pc.Color(1, 0.8, 0.5),
      intensity: 1.5,
      range: 10,
    })
    playerLight.setPosition(0, 2, 0)
    player.addChild(playerLight)

    // Load default model
    const defaultModel = CHARACTER_MODELS.find(m => m.id === selectedModelRef.current)!
    loadModel(defaultModel)

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

      const input = joystickInputRef.current
      const currentPos = player.getPosition()

      const newX = currentPos.x + input.x * playerSpeed * dt
      const newZ = currentPos.z - input.y * playerSpeed * dt

      const clampedX = Math.max(-18, Math.min(18, newX))
      const clampedZ = Math.max(-18, Math.min(18, newZ))

      const isMoving = Math.abs(input.x) > 0.1 || Math.abs(input.y) > 0.1

      player.setPosition(clampedX, 0, clampedZ)

      // Rotate player to face movement direction
      if (isMoving) {
        const targetAngle = Math.atan2(input.x, -input.y) * (180 / Math.PI)
        const currentAngle = player.getEulerAngles().y
        let angleDiff = targetAngle - currentAngle
        while (angleDiff > 180) angleDiff -= 360
        while (angleDiff < -180) angleDiff += 360
        player.setLocalEulerAngles(0, currentAngle + angleDiff * 0.15, 0)
      }

      // Animation state machine
      if (isMoving) {
        const speed = Math.sqrt(input.x * input.x + input.y * input.y)
        if (speed > 0.7) {
          playAnimation('run')
        } else {
          playAnimation('walk')
        }
      } else {
        playAnimation('idle')
      }

      // Sphere pulse effect
      const playerModel = playerModelRef.current
      if (playerModel && selectedModelRef.current === 'sphere') {
        const pulseScale = 1 + Math.sin(lastTime * 4) * 0.05
        playerModel.setLocalScale(pulseScale, pulseScale, pulseScale)
      }

      // Camera follows player
      const camTarget = new pc.Vec3(clampedX, 14, clampedZ + 14)
      const camPos = camera.getPosition()
      camPos.lerp(camPos, camTarget, 0.05)
      camera.setPosition(camPos)

      // Crystal collision
      const playerPos = player.getPosition()
      const checkPos = new pc.Vec3(playerPos.x, playerPos.y + 1, playerPos.z)
      const crystalsToRemove: pc.Entity[] = []

      crystalsRef.current.forEach((crystal) => {
        if (!crystal.parent) return

        const rot = crystal.getLocalEulerAngles()
        crystal.setLocalEulerAngles(rot.x, rot.y + 90 * dt, rot.z + 45 * dt)

        const crystalPos = crystal.getPosition()
        crystal.setPosition(crystalPos.x, 1.0 + Math.sin(lastTime * 3 + crystalPos.x) * 0.3, crystalPos.z)

        const dist = checkPos.distance(crystalPos)
        if (dist < 1.8) {
          crystalsToRemove.push(crystal)
          gs.score += 10
          gs.crystalsCollected++
          setGameState({ ...gs })
        }
      })

      crystalsToRemove.forEach(crystal => {
        spawnParticles(crystal.getPosition(), new pc.Color(1, 0.8, 0.2))
        if (crystal.parent) crystal.parent.removeChild(crystal)
        crystal.destroy()
        crystalsRef.current = crystalsRef.current.filter(c => c !== crystal)
      })

      if (crystalsRef.current.length === 0) {
        gs.score += gs.timeLeft * 5
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
          p.entity.setPosition(pPos.x + p.velocity.x * dt, pPos.y + p.velocity.y * dt, pPos.z + p.velocity.z * dt)
          p.velocity.y -= 9.8 * dt
          const scale = p.life * 0.15
          p.entity.setLocalScale(scale, scale, scale)
        }
      })
      particlesToRemove.reverse().forEach(i => {
        particlesRef.current.splice(i, 1)
      })
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

      {gameState.isPlaying && (
        <Hud score={gameState.score} timeLeft={gameState.timeLeft} crystalsCollected={gameState.crystalsCollected} totalCrystals={gameState.totalCrystals} />
      )}

      {gameState.isPlaying && (
        <Joystick onMove={handleJoystick} />
      )}

      {!gameState.isPlaying && !gameState.isGameOver && isLoaded && (
        <ModelSelector models={CHARACTER_MODELS} selectedModel={selectedModel} onSelect={handleModelChange} isLoading={modelLoading} />
      )}

      {!gameState.isPlaying && !gameState.isGameOver && isLoaded && (
        <StartScreen onStart={startGame} />
      )}

      {gameState.isGameOver && (
        <GameOverScreen score={gameState.score} crystalsCollected={gameState.crystalsCollected} totalCrystals={gameState.totalCrystals} won={allCrystalsCollected} onRestart={restartGame} />
      )}

      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/80 z-50">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-orange-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-white text-lg font-medium">Cargando...</p>
          </div>
        </div>
      )}

      {modelLoading && isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40 z-25 pointer-events-none">
          <div className="text-center bg-black/60 backdrop-blur-sm rounded-xl p-4">
            <div className="w-8 h-8 border-3 border-orange-400 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-white text-sm font-medium">Cargando modelo...</p>
          </div>
        </div>
      )}
    </div>
  )
}
