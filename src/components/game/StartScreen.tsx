'use client'

interface StartScreenProps {
  onStart: () => void
}

export function StartScreen({ onStart }: StartScreenProps) {
  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="text-center px-8 max-w-sm">
        {/* Logo */}
        <div className="mb-6">
          <div className="w-20 h-20 mx-auto rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center shadow-lg shadow-orange-500/30">
            <span className="text-4xl">💎</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-4xl font-black text-white mb-2 tracking-tight">
          Crystal<span className="text-orange-400">Rush</span>
        </h1>
        <p className="text-white/50 text-sm mb-8">
          Recoge todos los cristales antes de que se acabe el tiempo
        </p>

        {/* Instructions */}
        <div className="bg-white/5 rounded-xl p-4 mb-8 border border-white/10">
          <div className="space-y-3 text-left">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-lg">🕹️</span>
              </div>
              <p className="text-white/70 text-sm">Usa el joystick para mover tu esfera</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-lg">💎</span>
              </div>
              <p className="text-white/70 text-sm">Recoge los 20 cristales brillantes</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center flex-shrink-0">
                <span className="text-lg">⏱️</span>
              </div>
              <p className="text-white/70 text-sm">Tienes 60 segundos. El tiempo restante es bonus</p>
            </div>
          </div>
        </div>

        {/* Start Button */}
        <button
          onClick={onStart}
          className="w-full py-4 px-8 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 text-white font-bold text-lg rounded-xl shadow-lg shadow-orange-500/30 active:scale-95 transition-all duration-150"
        >
          JUGAR
        </button>

        <p className="text-white/20 text-xs mt-4">Hecho con PlayCanvas Engine</p>
      </div>
    </div>
  )
}
