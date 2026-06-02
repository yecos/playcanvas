/**
 * PlayCanvas REST API Client
 * Server-side only - handles authentication and API calls
 */

const PLAYCANVAS_API_BASE = 'https://playcanvas.com/api';

interface PlayCanvasConfig {
  accessToken: string;
}

interface ApiResponse<T = unknown> {
  status: number;
  data: T;
}

// Apps
export interface PlayCanvasApp {
  url: string;
  name: string;
  owner: string;
  project_id: number;
  plays: number;
  private: boolean;
  collaborator: boolean;
  tags: string[];
  description: string;
  thumbnails?: Record<string, string>;
}

// Assets
export interface PlayCanvasAsset {
  id: number;
  createdAt: string;
  modifiedAt: string;
  name: string;
  type: string;
  scope: { type: string; id: number };
  source: boolean;
  tags: string[];
  preload: boolean;
  exclude: boolean;
  sourceId: number | null;
  state: string;
  parent: number | null;
  hasThumbnail?: boolean;
  file?: {
    filename: string;
    size: number;
    hash: string;
    url: string;
    variants?: Record<string, unknown>;
  };
}

// Scenes
export interface PlayCanvasScene {
  id: number;
  projectId: number;
  name: string;
  created: string;
  modified: string;
}

// Branches
export interface PlayCanvasBranch {
  id: string;
  name: string;
  projectId: number;
  createdAt: string;
  updatedAt: string;
}

// Jobs
export interface PlayCanvasJob {
  id: number;
  status: 'running' | 'complete' | 'error';
  data?: Record<string, unknown>;
}

export class PlayCanvasClient {
  private accessToken: string;

  constructor(accessToken: string) {
    this.accessToken = accessToken;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const url = `${PLAYCANVAS_API_BASE}${path}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Accept': 'application/json',
        'User-Agent': 'PlayCanvas-Dashboard/1.0',
        ...options.headers,
      },
    });

    if (!response.ok && response.status !== 404) {
      const text = await response.text();
      try {
        const error = JSON.parse(text);
        throw new Error(error.error || `API Error: ${response.status}`);
      } catch {
        throw new Error(`API Error: ${response.status} - ${text.substring(0, 200)}`);
      }
    }

    const data = await response.json();
    return { status: response.status, data: data as T };
  }

  // ==================== Apps ====================

  async listApps(): Promise<PlayCanvasApp[]> {
    const result = await this.request<{ result: PlayCanvasApp[] }>('/apps');
    return result.data.result;
  }

  async getApp(appId: number): Promise<PlayCanvasApp> {
    const result = await this.request<PlayCanvasApp>(`/apps/${appId}`);
    return result.data;
  }

  async getPrimaryApp(projectId: number): Promise<PlayCanvasApp> {
    const result = await this.request<PlayCanvasApp>(`/projects/${projectId}/apps`);
    return result.data;
  }

  // ==================== Assets ====================

  async listAssets(projectId: number, branchId?: string, options?: { limit?: number; skip?: number }): Promise<{ result: PlayCanvasAsset[]; pagination: { skip: number; limit: number; total: number } }> {
    let path = `/projects/${projectId}/assets?limit=${options?.limit || 100000}`;
    if (branchId) path += `&branchId=${branchId}`;
    if (options?.skip) path += `&skip=${options.skip}`;
    const result = await this.request<{ result: PlayCanvasAsset[]; pagination: { skip: number; limit: number; total: number } }>(path);
    return result.data;
  }

  async getAsset(assetId: number, branchId?: string): Promise<PlayCanvasAsset> {
    let path = `/assets/${assetId}`;
    if (branchId) path += `?branchId=${branchId}`;
    const result = await this.request<PlayCanvasAsset>(path);
    return result.data;
  }

  async getAssetFile(assetId: number, branchId?: string): Promise<string> {
    let path = `/assets/${assetId}/file`;
    if (branchId) path += `?branchId=${branchId}`;
    const url = `${PLAYCANVAS_API_BASE}${path}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'User-Agent': 'PlayCanvas-Dashboard/1.0',
      },
    });
    return response.text();
  }

  async getAssetFileByUrl(fileUrl: string): Promise<string> {
    // fileUrl from the PlayCanvas API already includes /api/ prefix (e.g. /api/assets/123/file?branchId=...)
    // so we must not double it — use the base domain only
    const baseUrl = 'https://playcanvas.com';
    const url = `${baseUrl}${fileUrl}`;
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'User-Agent': 'PlayCanvas-Dashboard/1.0',
      },
    });
    return response.text();
  }

  async createAsset(params: {
    name: string;
    projectId: number;
    branchId?: string;
    type: string;
    file?: File | Blob;
    parent?: number;
    preload?: boolean;
  }): Promise<PlayCanvasAsset> {
    const formData = new FormData();
    formData.append('name', params.name);
    formData.append('projectId', params.projectId.toString());
    if (params.branchId) formData.append('branchId', params.branchId);
    formData.append('type', params.type);
    if (params.file) formData.append('file', params.file);
    if (params.parent) formData.append('parent', params.parent.toString());
    if (params.preload !== undefined) formData.append('preload', params.preload.toString());

    const result = await this.request<PlayCanvasAsset>('/assets', {
      method: 'POST',
      body: formData,
    });
    return result.data;
  }

  async updateAssetFile(assetId: number, file: Blob, branchId?: string): Promise<PlayCanvasAsset> {
    const formData = new FormData();
    formData.append('file', file);
    if (branchId) formData.append('branchId', branchId);

    const result = await this.request<PlayCanvasAsset>(`/assets/${assetId}`, {
      method: 'PUT',
      body: formData,
    });
    return result.data;
  }

  async deleteAsset(assetId: number, branchId?: string): Promise<void> {
    let path = `/assets/${assetId}`;
    if (branchId) path += `?branchId=${branchId}`;
    await this.request(path, { method: 'DELETE' });
  }

  // ==================== Scenes ====================

  async listScenes(projectId: number, branchId?: string): Promise<PlayCanvasScene[]> {
    let path = `/projects/${projectId}/scenes`;
    if (branchId) path += `?branchId=${branchId}`;
    const result = await this.request<{ result: PlayCanvasScene[] }>(path);
    return result.data.result;
  }

  // ==================== Branches ====================

  async listBranches(projectId: number): Promise<PlayCanvasBranch[]> {
    const result = await this.request<{ result: PlayCanvasBranch[] }>(`/projects/${projectId}/branches`);
    return result.data.result;
  }

  async createBranch(params: { name: string; projectId: number; sourceBranchId: string }): Promise<PlayCanvasBranch> {
    const result = await this.request<PlayCanvasBranch>('/branches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return result.data;
  }

  // ==================== Jobs ====================

  async getJob(jobId: number): Promise<PlayCanvasJob> {
    const result = await this.request<PlayCanvasJob>(`/jobs/${jobId}`);
    return result.data;
  }

  // ==================== Build ====================

  async downloadBuild(params: {
    projectId: number;
    name: string;
    scenes: number[];
    branchId?: string;
    format?: 'static' | 'npm';
  }): Promise<number> {
    const result = await this.request<{ id: number }>('/apps/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_id: params.projectId,
        name: params.name,
        scenes: params.scenes,
        branch_id: params.branchId,
        format: params.format || 'npm',
      }),
    });
    return result.data.id;
  }

  // ==================== Export ====================

  async exportProject(projectId: number, branchId?: string): Promise<number> {
    let path = `/projects/${projectId}/export`;
    if (branchId) path += `?branch_id=${branchId}`;
    const result = await this.request<{ id: number }>(path, {
      method: 'POST',
    });
    return result.data.id;
  }

  // ==================== Checkpoints ====================

  async createCheckpoint(params: { projectId: number; branchId: string; description: string }): Promise<number> {
    const result = await this.request<{ id: number }>('/checkpoints', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return result.data.id;
  }
}

// Singleton instance management
let clientInstance: PlayCanvasClient | null = null;

export function getPlayCanvasClient(accessToken?: string): PlayCanvasClient {
  if (accessToken) {
    clientInstance = new PlayCanvasClient(accessToken);
  }
  if (!clientInstance) {
    throw new Error('PlayCanvas client not initialized. Provide an access token.');
  }
  return clientInstance;
}
