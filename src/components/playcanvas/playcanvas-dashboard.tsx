'use client';

import { useEffect } from 'react';
import { usePlayCanvasStore } from '@/store/playcanvas-store';
import { usePlayCanvasApi } from '@/lib/use-playcanvas-api';
import { ProjectSelector } from '@/components/playcanvas/project-selector';
import { OverviewPanel } from '@/components/playcanvas/overview-panel';
import { AssetBrowser } from '@/components/playcanvas/asset-browser';
import { ScriptEditor } from '@/components/playcanvas/script-editor';
import { BuildPanel } from '@/components/playcanvas/build-panel';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2, Gamepad2, Box, Code2, Rocket, LayoutDashboard } from 'lucide-react';

export default function PlayCanvasDashboard() {
  const { 
    selectedProject, 
    activeTab, 
    setActiveTab, 
    isLoading,
    accessToken 
  } = usePlayCanvasStore();

  const { loadApps, loadProjectDetails } = usePlayCanvasApi();

  // Load apps on mount
  useEffect(() => {
    if (accessToken) {
      loadApps();
    }
  }, [accessToken, loadApps]);

  // Load project details when project changes
  useEffect(() => {
    if (selectedProject) {
      loadProjectDetails(selectedProject.projectId);
    }
  }, [selectedProject, loadProjectDetails]);

  if (!accessToken) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center p-8">
          <Gamepad2 className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
          <h1 className="text-3xl font-bold text-white mb-2">PlayCanvas Editor</h1>
          <p className="text-slate-400">Configurando acceso...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-500/20 flex items-center justify-center">
              <Gamepad2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">PlayCanvas Editor</h1>
              <p className="text-xs text-slate-400">Dashboard de Control</p>
            </div>
          </div>
          <ProjectSelector />
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-4">
        {!selectedProject ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Box className="w-16 h-16 text-slate-600 mb-4" />
            <h2 className="text-xl font-semibold text-slate-300 mb-2">Selecciona un Proyecto</h2>
            <p className="text-slate-500">Elige un proyecto de la lista para comenzar a editar</p>
          </div>
        ) : isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
            <span className="ml-3 text-slate-300">Cargando proyecto...</span>
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)} className="space-y-4">
            <TabsList className="bg-slate-800/50 border border-slate-700/50 w-full grid grid-cols-5 h-12">
              <TabsTrigger value="overview" className="flex items-center gap-2 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
                <LayoutDashboard className="w-4 h-4" />
                <span className="hidden sm:inline">Overview</span>
              </TabsTrigger>
              <TabsTrigger value="assets" className="flex items-center gap-2 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
                <Box className="w-4 h-4" />
                <span className="hidden sm:inline">Assets</span>
              </TabsTrigger>
              <TabsTrigger value="scripts" className="flex items-center gap-2 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
                <Code2 className="w-4 h-4" />
                <span className="hidden sm:inline">Scripts</span>
              </TabsTrigger>
              <TabsTrigger value="editor" className="flex items-center gap-2 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
                <Code2 className="w-4 h-4" />
                <span className="hidden sm:inline">Editor</span>
              </TabsTrigger>
              <TabsTrigger value="build" className="flex items-center gap-2 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400">
                <Rocket className="w-4 h-4" />
                <span className="hidden sm:inline">Build</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <OverviewPanel />
            </TabsContent>
            <TabsContent value="assets">
              <AssetBrowser />
            </TabsContent>
            <TabsContent value="scripts">
              <ScriptEditor />
            </TabsContent>
            <TabsContent value="editor">
              <ScriptEditor advanced />
            </TabsContent>
            <TabsContent value="build">
              <BuildPanel />
            </TabsContent>
          </Tabs>
        )}
      </main>
    </div>
  );
}
