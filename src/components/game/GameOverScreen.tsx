'use client'

interface GameOverScreenProps {
  score: number
  crystalsCollected: number
  totalCrystals: number
  won: boolean
  onRestart: () => void
}

export function GameOverScreen({ score, crystalsCollected, totalCrystals, won, onRestart }: GameOverScreenProps) {
  return (
    <div className="absolute inset-0 z-40 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="text-center px-8 max-w-sm">
        <div className="mb-6">
          <div className={`w-24 h-24 mx-auto rounded-full flex items-center justify-center shadow-lg ${
            won
              ? 'bg-gradient-to-br from-emerald-400 to-emerald-600 shadow-emerald-500/30'
              : 'bg-gradient-to-br from-red-400 to-red-600 shadow-red-500/30'
          }`}>
            <span className="text-5xl">{won ? '🏆' : '⏰'}</span>
          </div>
        </div>

        <h1 className="text-3xl font-black text-white mb-2">
          {won ? '¡Victoria!' : '¡Se acabó el tiempo!'}
        </h1>
        <p className="text-white/50 text-sm mb-8">
          {won ? 'Recogiste todos los cristales' : 'No recogiste todos los cristales a tiempo'}
        </p>

        <div className="bg-white/5 rounded-xl p-5 mb-8 border border-white/10 space-y-4">
          <div className="flex justify-between items-center">
            <span className="text-white/50 text-sm">Puntuación</span>
            <span className="text-2xl font-bold text-orange-400">{score}</span>
          </div>
          <div className="h-px bg-white/10" />
          <div className="flex justify-between items-center">
            <span className="text-white/50 text-sm">Cristales</span>
            <span className="text-lg font-semibold text-cyan-400">
              {crystalsCollected}/{totalCrystals}
            </span>
          </div>
          {won && (
            <>
              <div className="h-px bg-white/10" />
              <div className="flex justify-between items-center">
                <span className="text-white/50 text-sm">Bonus de tiempo</span>
                <span className="text-lg font-semibold text-emerald-400">+{Math.max(0, score - crystalsCollected * 10)}</span>
              </div>
            </>
          )}
        </div>

        <button
          onClick={onRestart}
          className="w-full py-4 px-8 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-500 text-white font-bold text-lg rounded-xl shadow-lg shadow-orange-500/30 active:scale-95 transition-all duration-150"
        >
          JUGAR DE NUEVO
        </button>
      </div>
    </div>
  )
}
