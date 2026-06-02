'use client';

import { usePlayCanvasStore } from '@/store/playcanvas-store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Box, FileCode, ImageIcon, Film, Palette, Folder, FileText, 
  Layers, Eye, ExternalLink 
} from 'lucide-react';

const TYPE_ICONS: Record<string, React.ReactNode> = {
  container: <Box className="w-4 h-4" />,
  model: <Box className="w-4 h-4" />,
  texture: <ImageIcon className="w-4 h-4" />,
  material: <Palette className="w-4 h-4" />,
  animation: <Film className="w-4 h-4" />,
  script: <FileCode className="w-4 h-4" />,
  folder: <Folder className="w-4 h-4" />,
  json: <FileText className="w-4 h-4" />,
  render: <Layers className="w-4 h-4" />,
  scene: <Eye className="w-4 h-4" />,
  template: <Layers className="w-4 h-4" />,
  animstategraph: <Film className="w-4 h-4" />,
};

const TYPE_COLORS: Record<string, string> = {
  container: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  model: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  texture: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  material: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  animation: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  script: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  folder: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  json: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  render: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  scene: 'bg-green-500/20 text-green-400 border-green-500/30',
  template: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  animstategraph: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
};

export function OverviewPanel() {
  const { selectedProject, assetsByType, totalAssets, scenes } = usePlayCanvasStore();

  if (!selectedProject) return null;

  const sortedTypes = Object.entries(assetsByType).sort((a, b) => b[1] - a[1]);

  return (
    <div className="space-y-6">
      {/* Project Info */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-white text-lg">{selectedProject.name}</CardTitle>
            <a
              href={selectedProject.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300"
            >
              <ExternalLink className="w-3 h-3" />
              Abrir
            </a>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-2xl font-bold text-emerald-400">{totalAssets.toLocaleString()}</div>
              <div className="text-xs text-slate-400 mt-1">Total Assets</div>
            </div>
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-2xl font-bold text-blue-400">{sortedTypes.length}</div>
              <div className="text-xs text-slate-400 mt-1">Tipos</div>
            </div>
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-2xl font-bold text-purple-400">{scenes.length}</div>
              <div className="text-xs text-slate-400 mt-1">Escenas</div>
            </div>
            <div className="text-center p-3 bg-slate-700/30 rounded-lg">
              <div className="text-2xl font-bold text-amber-400">{selectedProject.owner}</div>
              <div className="text-xs text-slate-400 mt-1">Owner</div>
            </div>
          </div>
          {selectedProject.description && (
            <p className="text-sm text-slate-400 mt-3">{selectedProject.description}</p>
          )}
        </CardContent>
      </Card>

      {/* Asset Types Grid */}
      <div>
        <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <Box className="w-4 h-4 text-emerald-400" />
          Assets por Tipo
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {sortedTypes.map(([type, count]) => (
            <Card key={type} className={`border ${TYPE_COLORS[type] || 'bg-slate-700/30 border-slate-600/30'} hover:scale-[1.02] transition-transform cursor-pointer`}>
              <CardContent className="p-3 flex items-center gap-3">
                <div className="shrink-0">
                  {TYPE_ICONS[type] || <Box className="w-4 h-4" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-medium truncate">{type}</div>
                  <div className="text-lg font-bold">{count.toLocaleString()}</div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Scenes */}
      <div>
        <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
          <Eye className="w-4 h-4 text-emerald-400" />
          Escenas
        </h3>
        <div className="grid gap-2">
          {scenes.map((scene) => (
            <Card key={scene.id} className="bg-slate-800/50 border-slate-700/50">
              <CardContent className="p-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-white">{scene.name}</div>
                  <div className="text-xs text-slate-500">ID: {scene.id}</div>
                </div>
                <Badge variant="outline" className="text-xs text-slate-400 border-slate-600">
                  Escena
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Quick Links */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-slate-300">Acciones Rápidas</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <a
            href={`https://playcanvas.com/editor/scene/${scenes[0]?.id || ''}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 p-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 transition-colors text-emerald-400 text-sm"
          >
            <ExternalLink className="w-4 h-4" />
            Abrir en PlayCanvas Editor
          </a>
          <a
            href={selectedProject.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 p-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 transition-colors text-blue-400 text-sm"
          >
            <Eye className="w-4 h-4" />
            Ver App Publicada
          </a>
        </CardContent>
      </Card>
    </div>
  );
}
