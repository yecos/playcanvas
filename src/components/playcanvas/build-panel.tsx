'use client';

import { useState } from 'react';
import { usePlayCanvasStore } from '@/store/playcanvas-store';
import { usePlayCanvasApi } from '@/lib/use-playcanvas-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Rocket, Loader2, ExternalLink, Download, GitBranch,
  CheckCircle, AlertCircle, Clock
} from 'lucide-react';
import { toast } from 'sonner';

export function BuildPanel() {
  const { selectedProject, scenes, assetsByType } = usePlayCanvasStore();
  const [isBuilding, setIsBuilding] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [buildStatus, setBuildStatus] = useState<string | null>(null);

  if (!selectedProject) return null;

  const scriptCount = assetsByType['script'] || 0;
  const sceneCount = scenes.length;

  return (
    <div className="space-y-6">
      {/* Build Options */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Rocket className="w-5 h-5 text-emerald-400" />
            Build & Publicar
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 bg-slate-700/30 rounded-lg">
              <div className="text-xs text-slate-400">Proyecto</div>
              <div className="text-sm font-medium text-white">{selectedProject.name}</div>
            </div>
            <div className="p-3 bg-slate-700/30 rounded-lg">
              <div className="text-xs text-slate-400">ID</div>
              <div className="text-sm font-medium text-white font-mono">{selectedProject.projectId}</div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-sm font-medium text-slate-300">Escenas a incluir</h4>
            {scenes.map((scene) => (
              <div key={scene.id} className="flex items-center gap-2 p-2 bg-slate-700/20 rounded">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-white flex-1">{scene.name}</span>
                <Badge variant="outline" className="text-xs text-slate-500 border-slate-600">
                  ID: {scene.id}
                </Badge>
              </div>
            ))}
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <Button
              className="flex-1 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30"
              disabled={isBuilding}
              onClick={async () => {
                setIsBuilding(true);
                setBuildStatus('building');
                try {
                  const response = await fetch('/api/playcanvas/build', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'x-playcanvas-token': usePlayCanvasStore.getState().accessToken,
                    },
                    body: JSON.stringify({
                      projectId: selectedProject.projectId,
                      name: selectedProject.name,
                      scenes: scenes.map((s) => s.id),
                      format: 'npm',
                    }),
                  });
                  const data = await response.json();
                  if (data.jobId) {
                    setBuildStatus('started');
                    toast.success(`Build iniciado. Job ID: ${data.jobId}`);
                  } else {
                    setBuildStatus('error');
                    toast.error(data.error || 'Error al iniciar build');
                  }
                } catch (err) {
                  setBuildStatus('error');
                  toast.error('Error al iniciar build');
                }
                setIsBuilding(false);
              }}
            >
              {isBuilding ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Rocket className="w-4 h-4 mr-2" />
              )}
              Build App (NPM)
            </Button>

            <Button
              variant="outline"
              className="flex-1 border-slate-600 text-slate-300 hover:bg-slate-700"
              disabled={isExporting}
              onClick={async () => {
                setIsExporting(true);
                try {
                  const response = await fetch('/api/playcanvas/export', {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                      'x-playcanvas-token': usePlayCanvasStore.getState().accessToken,
                    },
                    body: JSON.stringify({
                      projectId: selectedProject.projectId,
                    }),
                  });
                  const data = await response.json();
                  if (data.jobId) {
                    toast.success(`Exportación iniciada. Job ID: ${data.jobId}`);
                  } else {
                    toast.error(data.error || 'Error al exportar');
                  }
                } catch (err) {
                  toast.error('Error al exportar proyecto');
                }
                setIsExporting(false);
              }}
            >
              {isExporting ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              Exportar ZIP
            </Button>
          </div>

          {buildStatus && (
            <div className={`p-3 rounded-lg flex items-center gap-2 text-sm ${
              buildStatus === 'building' ? 'bg-amber-500/10 text-amber-400' :
              buildStatus === 'started' ? 'bg-emerald-500/10 text-emerald-400' :
              'bg-red-500/10 text-red-400'
            }`}>
              {buildStatus === 'building' && <Loader2 className="w-4 h-4 animate-spin" />}
              {buildStatus === 'started' && <CheckCircle className="w-4 h-4" />}
              {buildStatus === 'error' && <AlertCircle className="w-4 h-4" />}
              {buildStatus === 'building' ? 'Construyendo...' :
               buildStatus === 'started' ? 'Build iniciado exitosamente' :
               'Error en el build'}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Links */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-sm text-slate-300">Enlaces Rápidos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <a
            href={selectedProject.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 p-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 transition-colors text-blue-400 text-sm"
          >
            <ExternalLink className="w-4 h-4" />
            Ver App Publicada
          </a>
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
            href={`https://playcanvas.com/project/${selectedProject.projectId}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 p-2 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 transition-colors text-purple-400 text-sm"
          >
            <ExternalLink className="w-4 h-4" />
            Página del Proyecto
          </a>
        </CardContent>
      </Card>

      {/* Project Stats */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-sm text-slate-300">Estadísticas del Proyecto</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="text-center p-2 bg-slate-700/20 rounded">
              <div className="text-lg font-bold text-emerald-400">{scriptCount}</div>
              <div className="text-xs text-slate-500">Scripts</div>
            </div>
            <div className="text-center p-2 bg-slate-700/20 rounded">
              <div className="text-lg font-bold text-blue-400">{sceneCount}</div>
              <div className="text-xs text-slate-500">Escenas</div>
            </div>
            <div className="text-center p-2 bg-slate-700/20 rounded">
              <div className="text-lg font-bold text-amber-400">{assetsByType['model'] || 0}</div>
              <div className="text-xs text-slate-500">Modelos</div>
            </div>
            <div className="text-center p-2 bg-slate-700/20 rounded">
              <div className="text-lg font-bold text-purple-400">{assetsByType['texture'] || 0}</div>
              <div className="text-xs text-slate-500">Texturas</div>
            </div>
            <div className="text-center p-2 bg-slate-700/20 rounded">
              <div className="text-lg font-bold text-pink-400">{assetsByType['material'] || 0}</div>
              <div className="text-xs text-slate-500">Materiales</div>
            </div>
            <div className="text-center p-2 bg-slate-700/20 rounded">
              <div className="text-lg font-bold text-cyan-400">{assetsByType['animation'] || 0}</div>
              <div className="text-xs text-slate-500">Animaciones</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
