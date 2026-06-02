'use client';

import { useState, useMemo } from 'react';
import { usePlayCanvasStore } from '@/store/playcanvas-store';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Box, FileCode, ImageIcon, Film, Palette, Folder, FileText,
  Layers, Eye, Search, ChevronRight, Clock
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
  container: 'text-blue-400',
  model: 'text-blue-400',
  texture: 'text-purple-400',
  material: 'text-pink-400',
  animation: 'text-amber-400',
  script: 'text-emerald-400',
  folder: 'text-slate-400',
  json: 'text-orange-400',
  render: 'text-cyan-400',
  scene: 'text-green-400',
  template: 'text-indigo-400',
  animstategraph: 'text-amber-400',
};

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return 'Hoy';
  if (days === 1) return 'Ayer';
  if (days < 30) return `Hace ${days} días`;
  return date.toLocaleDateString();
}

export function AssetBrowser() {
  const { assets, assetsByType, totalAssets, selectedAssetType, setSelectedAssetType, setSelectedAsset } = usePlayCanvasStore();
  const [searchQuery, setSearchQuery] = useState('');

  const sortedTypes = useMemo(() => 
    Object.entries(assetsByType).sort((a, b) => b[1] - a[1]),
    [assetsByType]
  );

  const filteredAssets = useMemo(() => {
    let filtered = assets;
    
    if (selectedAssetType !== 'all') {
      filtered = filtered.filter((a) => a.type === selectedAssetType);
    }
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter((a) => 
        a.name.toLowerCase().includes(query) ||
        a.type.toLowerCase().includes(query) ||
        a.tags.some((t) => t.toLowerCase().includes(query))
      );
    }
    
    return filtered;
  }, [assets, selectedAssetType, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Search and Stats */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Buscar assets por nombre, tipo o tag..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
          />
        </div>
        <div className="text-sm text-slate-400 flex items-center gap-2 shrink-0">
          <span>{filteredAssets.length.toLocaleString()} de {totalAssets.toLocaleString()} assets</span>
        </div>
      </div>

      {/* Type Filter Chips */}
      <ScrollArea className="w-full whitespace-nowrap">
        <div className="flex gap-2 pb-2">
          <Badge
            variant={selectedAssetType === 'all' ? 'default' : 'outline'}
            className={`cursor-pointer ${selectedAssetType === 'all' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'text-slate-400 border-slate-600 hover:bg-slate-700'}`}
            onClick={() => setSelectedAssetType('all')}
          >
            Todos ({totalAssets.toLocaleString()})
          </Badge>
          {sortedTypes.map(([type, count]) => (
            <Badge
              key={type}
              variant={selectedAssetType === type ? 'default' : 'outline'}
              className={`cursor-pointer shrink-0 ${selectedAssetType === type ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'text-slate-400 border-slate-600 hover:bg-slate-700'}`}
              onClick={() => setSelectedAssetType(type)}
            >
              <span className={`mr-1 ${TYPE_COLORS[type] || 'text-slate-400'}`}>
                {TYPE_ICONS[type]}
              </span>
              {type} ({count.toLocaleString()})
            </Badge>
          ))}
        </div>
      </ScrollArea>

      {/* Asset List */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <ScrollArea className="max-h-[calc(100vh-320px)]">
          <div className="divide-y divide-slate-700/30">
            {filteredAssets.slice(0, 200).map((asset) => (
              <div
                key={asset.id}
                className="flex items-center gap-3 p-3 hover:bg-slate-700/20 cursor-pointer transition-colors"
                onClick={() => setSelectedAsset(asset)}
              >
                <div className={`shrink-0 ${TYPE_COLORS[asset.type] || 'text-slate-400'}`}>
                  {TYPE_ICONS[asset.type] || <Box className="w-4 h-4" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-white truncate">{asset.name}</div>
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <span className={TYPE_COLORS[asset.type] || 'text-slate-400'}>{asset.type}</span>
                    {asset.file && (
                      <>
                        <span>·</span>
                        <span>{formatFileSize(asset.file.size)}</span>
                      </>
                    )}
                    <span>·</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(asset.modifiedAt)}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  {asset.tags.slice(0, 2).map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs text-slate-500 border-slate-700 px-1.5 py-0">
                      {tag}
                    </Badge>
                  ))}
                </div>
                <ChevronRight className="w-4 h-4 text-slate-600 shrink-0" />
              </div>
            ))}
            {filteredAssets.length > 200 && (
              <div className="p-3 text-center text-sm text-slate-500">
                Mostrando 200 de {filteredAssets.length} assets. Usa el filtro para ver más.
              </div>
            )}
            {filteredAssets.length === 0 && (
              <div className="p-8 text-center text-slate-500">
                No se encontraron assets
              </div>
            )}
          </div>
        </ScrollArea>
      </Card>
    </div>
  );
}
