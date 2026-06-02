'use client'

interface HudProps {
  score: number
  timeLeft: number
  crystalsCollected: number
  totalCrystals: number
}

export function Hud({ score, timeLeft, crystalsCollected, totalCrystals }: HudProps) {
  const timeColor = timeLeft <= 10 ? 'text-red-400' : timeLeft <= 20 ? 'text-yellow-400' : 'text-emerald-400'
  const timeBg = timeLeft <= 10 ? 'from-red-500/20 to-red-900/20' : timeLeft <= 20 ? 'from-yellow-500/20 to-yellow-900/20' : 'from-emerald-500/20 to-emerald-900/20'

  return (
    <div className="absolute top-0 left-0 right-0 z-20 pointer-events-none">
      <div className="flex justify-between items-start p-4 gap-3">
        <div className="bg-black/50 backdrop-blur-md rounded-xl px-4 py-2 border border-white/10">
          <p className="text-white/50 text-xs font-medium uppercase tracking-wider">Puntos</p>
          <p className="text-2xl font-bold text-orange-400">{score}</p>
        </div>

        <div className="bg-black/50 backdrop-blur-md rounded-xl px-4 py-2 border border-white/10 flex-shrink-0">
          <p className="text-white/50 text-xs font-medium uppercase tracking-wider">Cristales</p>
          <p className="text-2xl font-bold text-cyan-400">
            {crystalsCollected}
            <span className="text-base text-white/40">/{totalCrystals}</span>
          </p>
        </div>

        <div className={`bg-gradient-to-br ${timeBg} backdrop-blur-md rounded-xl px-4 py-2 border border-white/10`}>
          <p className="text-white/50 text-xs font-medium uppercase tracking-wider">Tiempo</p>
          <p className={`text-2xl font-bold ${timeColor}`}>
            {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
          </p>
        </div>
      </div>
    </div>
  )
}
