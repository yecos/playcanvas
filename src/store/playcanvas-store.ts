import { create } from 'zustand';

export interface PlayCanvasProject {
  projectId: number;
  name: string;
  owner: string;
  url: string;
  description: string;
}

export interface AssetItem {
  id: number;
  name: string;
  type: string;
  createdAt: string;
  modifiedAt: string;
  parent: number | null;
  tags: string[];
  file?: {
    filename: string;
    size: number;
    hash: string;
    url: string;
  };
  hasThumbnail?: boolean;
}

export interface SceneItem {
  id: number;
  name: string;
  created: string;
  modified: string;
}

type TabType = 'overview' | 'assets' | 'scripts' | 'editor' | 'build';

interface PlayCanvasState {
  // Auth
  accessToken: string;
  setAccessToken: (token: string) => void;

  // Projects
  projects: PlayCanvasProject[];
  selectedProject: PlayCanvasProject | null;
  setProjects: (projects: PlayCanvasProject[]) => void;
  selectProject: (project: PlayCanvasProject) => void;

  // Assets
  assets: AssetItem[];
  assetsByType: Record<string, number>;
  totalAssets: number;
  setAssets: (assets: AssetItem[], byType: Record<string, number>, total: number) => void;
  
  // Scenes
  scenes: SceneItem[];
  setScenes: (scenes: SceneItem[]) => void;

  // UI State
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  selectedAssetType: string;
  setSelectedAssetType: (type: string) => void;
  selectedAsset: AssetItem | null;
  setSelectedAsset: (asset: AssetItem | null) => void;
  
  // Editor
  editorContent: string;
  setEditorContent: (content: string) => void;
  editorAssetId: number | null;
  setEditorAssetId: (id: number | null) => void;

  // Loading states
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  error: string | null;
  setError: (error: string | null) => void;
}

export const usePlayCanvasStore = create<PlayCanvasState>((set) => ({
  // Auth
  accessToken: 'SfQrMBrYQQkdHazNDt0yoE1gCrnTJek8',
  setAccessToken: (token) => set({ accessToken: token }),

  // Projects
  projects: [],
  selectedProject: null,
  setProjects: (projects) => set({ projects }),
  selectProject: (project) => set({ selectedProject: project }),

  // Assets
  assets: [],
  assetsByType: {},
  totalAssets: 0,
  setAssets: (assets, byType, total) => set({ assets, assetsByType: byType, totalAssets: total }),

  // Scenes
  scenes: [],
  setScenes: (scenes) => set({ scenes }),

  // UI State
  activeTab: 'overview',
  setActiveTab: (tab) => set({ activeTab: tab }),
  selectedAssetType: 'all',
  setSelectedAssetType: (type) => set({ selectedAssetType: type }),
  selectedAsset: null,
  setSelectedAsset: (asset) => set({ selectedAsset: asset }),

  // Editor
  editorContent: '',
  setEditorContent: (content) => set({ editorContent: content }),
  editorAssetId: null,
  setEditorAssetId: (id) => set({ editorAssetId: id }),

  // Loading states
  isLoading: false,
  setLoading: (loading) => set({ isLoading: loading }),
  error: null,
  setError: (error) => set({ error }),
}));
