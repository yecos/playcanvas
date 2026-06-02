'use client';

import { useState, useCallback } from 'react';
import { usePlayCanvasStore } from '@/store/playcanvas-store';
import { usePlayCanvasApi } from '@/lib/use-playcanvas-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
import { 
  FileCode, Save, Loader2, Play, Eye, Copy, Download,
  ChevronRight, RefreshCw, Plus, Trash2
} from 'lucide-react';
import { toast } from 'sonner';

export function ScriptEditor({ advanced = false }: { advanced?: boolean }) {
  const { assets, selectedAsset, setSelectedAsset, editorContent, setEditorContent, editorAssetId, setEditorAssetId } = usePlayCanvasStore();
  const { getAssetContent, updateAssetContent } = usePlayCanvasApi();
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [originalContent, setOriginalContent] = useState('');
  const [hasChanges, setHasChanges] = useState(false);

  const scripts = assets.filter((a) => a.type === 'script');

  const loadScriptContent = useCallback(async (assetId: number) => {
    setIsLoadingContent(true);
    const content = await getAssetContent(assetId);
    if (content !== null) {
      setEditorContent(content);
      setOriginalContent(content);
      setEditorAssetId(assetId);
      setHasChanges(false);
    }
    setIsLoadingContent(false);
  }, [getAssetContent, setEditorContent, setEditorAssetId]);

  const handleContentChange = (value: string) => {
    setEditorContent(value);
    setHasChanges(value !== originalContent);
  };

  const handleSave = async () => {
    if (!editorAssetId) return;
    setIsSaving(true);
    const success = await updateAssetContent(editorAssetId, editorContent);
    if (success) {
      setOriginalContent(editorContent);
      setHasChanges(false);
      toast.success('Script guardado exitosamente');
    } else {
      toast.error('Error al guardar el script');
    }
    setIsSaving(false);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(editorContent);
    toast.success('Código copiado al portapapeles');
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4 h-[calc(100vh-200px)]">
      {/* Script List Sidebar */}
      <Card className="bg-slate-800/50 border-slate-700/50 flex flex-col">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm text-slate-300 flex items-center gap-2">
            <FileCode className="w-4 h-4 text-emerald-400" />
            Scripts ({scripts.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 p-0">
          <ScrollArea className="h-full max-h-[calc(100vh-280px)]">
            <div className="divide-y divide-slate-700/30">
              {scripts.map((script) => (
                <div
                  key={script.id}
                  className={`flex items-center gap-2 p-3 cursor-pointer transition-colors ${
                    editorAssetId === script.id
                      ? 'bg-emerald-500/10 border-l-2 border-emerald-400'
                      : 'hover:bg-slate-700/20 border-l-2 border-transparent'
                  }`}
                  onClick={() => loadScriptContent(script.id)}
                >
                  <FileCode className={`w-4 h-4 shrink-0 ${editorAssetId === script.id ? 'text-emerald-400' : 'text-slate-500'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-white truncate">{script.name}</div>
                    <div className="text-xs text-slate-500">ID: {script.id}</div>
                  </div>
                  <ChevronRight className="w-3 h-3 text-slate-600 shrink-0" />
                </div>
              ))}
              {scripts.length === 0 && (
                <div className="p-4 text-center text-slate-500 text-sm">
                  No hay scripts en este proyecto
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Editor Area */}
      <Card className="bg-slate-800/50 border-slate-700/50 flex flex-col">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm text-slate-300 flex items-center gap-2">
              {editorAssetId ? (
                <>
                  <FileCode className="w-4 h-4 text-emerald-400" />
                  {scripts.find((s) => s.id === editorAssetId)?.name || 'Script'}
                </>
              ) : (
                'Selecciona un script para editar'
              )}
            </CardTitle>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <Badge variant="outline" className="text-xs text-amber-400 border-amber-500/30 bg-amber-500/10">
                  Sin guardar
                </Badge>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="text-slate-400 hover:text-white h-8"
                onClick={handleCopy}
                disabled={!editorContent}
              >
                <Copy className="w-3 h-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="text-slate-400 hover:text-white h-8"
                onClick={() => editorAssetId && loadScriptContent(editorAssetId)}
                disabled={!editorAssetId || isLoadingContent}
              >
                <RefreshCw className={`w-3 h-3 ${isLoadingContent ? 'animate-spin' : ''}`} />
              </Button>
              <Button
                size="sm"
                className="bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 h-8"
                onClick={handleSave}
                disabled={!editorAssetId || isSaving || !hasChanges}
              >
                {isSaving ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Save className="w-3 h-3" />
                )}
                <span className="ml-1 hidden sm:inline">Guardar</span>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="flex-1 p-0">
          {isLoadingContent ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
              <span className="ml-2 text-slate-400">Cargando script...</span>
            </div>
          ) : editorContent ? (
            <div className="relative h-full">
              {/* Line numbers */}
              <div className="absolute left-0 top-0 bottom-0 w-12 bg-slate-900/50 border-r border-slate-700/30 flex flex-col items-end pr-2 pt-3 text-xs text-slate-600 font-mono overflow-hidden pointer-events-none">
                {editorContent.split('\n').map((_, i) => (
                  <div key={i} className="leading-6">{i + 1}</div>
                ))}
              </div>
              <Textarea
                value={editorContent}
                onChange={(e) => handleContentChange(e.target.value)}
                className="w-full h-full resize-none bg-transparent border-0 text-emerald-300 font-mono text-sm leading-6 pl-14 pr-4 py-3 focus-visible:ring-0 focus-visible:ring-offset-0"
                style={{ tabSize: 2 }}
              />
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <FileCode className="w-12 h-12 mb-3 text-slate-700" />
              <p className="text-sm">Selecciona un script de la lista para editarlo</p>
              <p className="text-xs mt-1 text-slate-600">
                O crea uno nuevo con el botón +
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
