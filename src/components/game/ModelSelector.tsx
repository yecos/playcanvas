'use client'

interface ModelConfig {
  id: string
  name: string
  icon: string
  url: string | null
  scale: number
  yOffset: number
  description: string
}

interface ModelSelectorProps {
  models: ModelConfig[]
  selectedModel: string
  onSelect: (modelId: string) => void
  isLoading: boolean
}

export function ModelSelector({ models, selectedModel, onSelect, isLoading }: ModelSelectorProps) {
  return (
    <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30">
      <div className="bg-black/60 backdrop-blur-md rounded-2xl border border-white/10 p-3">
        <p className="text-white/40 text-xs font-medium text-center mb-2 uppercase tracking-wider">
          Elige tu personaje
        </p>
        <div className="flex gap-2">
          {models.map((model) => {
            const isSelected = selectedModel === model.id
            return (
              <button
                key={model.id}
                onClick={() => !isLoading && onSelect(model.id)}
                disabled={isLoading}
                className={`
                  relative flex flex-col items-center justify-center px-4 py-3 rounded-xl
                  transition-all duration-200 min-w-[80px]
                  ${isSelected
                    ? 'bg-orange-500/30 border-2 border-orange-400 shadow-lg shadow-orange-500/20'
                    : 'bg-white/5 border-2 border-white/10 hover:bg-white/10 hover:border-white/20'
                  }
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer active:scale-95'}
                `}
              >
                <span className="text-2xl mb-1">{model.icon}</span>
                <span className={`text-xs font-bold ${isSelected ? 'text-orange-300' : 'text-white/60'}`}>
                  {model.name}
                </span>
                {isSelected && (
                  <div className="absolute -top-1 -right-1 w-4 h-4 bg-orange-400 rounded-full flex items-center justify-center">
                    <span className="text-[8px] text-black font-bold">✓</span>
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
