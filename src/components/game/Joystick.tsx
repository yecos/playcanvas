'use client'

import { useRef, useCallback, useEffect } from 'react'

interface JoystickProps {
  onMove: (x: number, y: number) => void
}

export function Joystick({ onMove }: JoystickProps) {
  const baseRef = useRef<HTMLDivElement>(null)
  const knobRef = useRef<HTMLDivElement>(null)
  const isDragging = useRef(false)
  const centerRef = useRef({ x: 0, y: 0 })
  const maxDist = 50

  const updateKnob = useCallback((clientX: number, clientY: number) => {
    if (!knobRef.current || !baseRef.current) return

    const dx = clientX - centerRef.current.x
    const dy = clientY - centerRef.current.y
    const dist = Math.sqrt(dx * dx + dy * dy)
    const clampedDist = Math.min(dist, maxDist)
    const angle = Math.atan2(dy, dx)

    const knobX = Math.cos(angle) * clampedDist
    const knobY = Math.sin(angle) * clampedDist

    knobRef.current.style.transform = `translate(${knobX}px, ${knobY}px)`

    // Normalize to -1 to 1
    const normX = knobX / maxDist
    const normY = knobY / maxDist
    onMove(normX, normY)
  }, [onMove])

  const handleStart = useCallback((e: React.TouchEvent | React.MouseEvent) => {
    e.preventDefault()
    isDragging.current = true

    const rect = baseRef.current?.getBoundingClientRect()
    if (!rect) return

    centerRef.current = {
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2,
    }

    if ('touches' in e) {
      updateKnob(e.touches[0].clientX, e.touches[0].clientY)
    } else {
      updateKnob(e.clientX, e.clientY)
    }
  }, [updateKnob])

  const handleMove = useCallback((e: TouchEvent | MouseEvent) => {
    if (!isDragging.current) return
    e.preventDefault()

    if ('touches' in e) {
      updateKnob(e.touches[0].clientX, e.touches[0].clientY)
    } else {
      updateKnob(e.clientX, e.clientY)
    }
  }, [updateKnob])

  const handleEnd = useCallback(() => {
    isDragging.current = false
    if (knobRef.current) {
      knobRef.current.style.transform = 'translate(0px, 0px)'
    }
    onMove(0, 0)
  }, [onMove])

  useEffect(() => {
    window.addEventListener('touchmove', handleMove, { passive: false })
    window.addEventListener('mousemove', handleMove)
    window.addEventListener('touchend', handleEnd)
    window.addEventListener('mouseup', handleEnd)
    window.addEventListener('touchcancel', handleEnd)

    return () => {
      window.removeEventListener('touchmove', handleMove)
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('touchend', handleEnd)
      window.removeEventListener('mouseup', handleEnd)
      window.removeEventListener('touchcancel', handleEnd)
    }
  }, [handleMove, handleEnd])

  return (
    <div className="absolute bottom-8 left-8 z-30 select-none">
      {/* Direction labels */}
      <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-white/40 text-xs font-bold">▲</div>
      <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-white/40 text-xs font-bold">▼</div>
      <div className="absolute top-1/2 -left-5 -translate-y-1/2 text-white/40 text-xs font-bold">◄</div>
      <div className="absolute top-1/2 -right-5 -translate-y-1/2 text-white/40 text-xs font-bold">►</div>

      {/* Joystick base */}
      <div
        ref={baseRef}
        className="w-32 h-32 rounded-full bg-white/10 border-2 border-white/20 backdrop-blur-sm flex items-center justify-center cursor-pointer"
        onTouchStart={handleStart}
        onMouseDown={handleStart}
        style={{ touchAction: 'none' }}
      >
        {/* Joystick knob */}
        <div
          ref={knobRef}
          className="w-14 h-14 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 border-2 border-white/30 shadow-lg shadow-orange-500/30 transition-transform duration-75"
          style={{ touchAction: 'none' }}
        />
      </div>

      {/* Label */}
      <p className="text-white/30 text-xs text-center mt-6 font-medium">MOVER</p>
    </div>
  )
}
