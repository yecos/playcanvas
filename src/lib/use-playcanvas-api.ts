'use client';

import { useCallback } from 'react';
import { usePlayCanvasStore } from '@/store/playcanvas-store';

const API_BASE = '/api/playcanvas';

export function usePlayCanvasApi() {
  const { accessToken, setProjects, setAssets, setScenes, setLoading, setError } = usePlayCanvasStore();

  const fetchWithAuth = useCallback(async (path: string, options?: RequestInit) => {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'x-playcanvas-token': accessToken,
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || `API Error: ${response.status}`);
    }
    return response.json();
  }, [accessToken]);

  const loadApps = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWithAuth('/apps');
      const projects = data.apps.map((app: { project_id: number; name: string; owner: string; url: string; description: string }) => ({
        projectId: app.project_id,
        name: app.name,
        owner: app.owner,
        url: app.url,
        description: app.description,
      }));
      setProjects(projects);
      return projects;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load projects';
      setError(message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, setProjects, setLoading, setError]);

  const loadProjectDetails = useCallback(async (projectId: number) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchWithAuth(`/projects/${projectId}`);
      if (data.assets) {
        setAssets(
          data.assets.items || [],
          data.assets.byType || {},
          data.assets.total || 0
        );
      }
      if (data.scenes) {
        setScenes(data.scenes);
      }
      return data;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load project';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [fetchWithAuth, setAssets, setScenes, setLoading, setError]);

  const getAssetContent = useCallback(async (assetId: number, branchId?: string) => {
    try {
      const path = `/assets/${assetId}${branchId ? `?branchId=${branchId}` : ''}`;
      const data = await fetchWithAuth(path);
      return data.content;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load asset';
      setError(message);
      return null;
    }
  }, [fetchWithAuth, setError]);

  const updateAssetContent = useCallback(async (assetId: number, content: string, branchId?: string) => {
    try {
      const path = `/assets/${assetId}`;
      await fetchWithAuth(path, {
        method: 'PUT',
        body: JSON.stringify({ content, branchId }),
      });
      return true;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to update asset';
      setError(message);
      return false;
    }
  }, [fetchWithAuth, setError]);

  return {
    loadApps,
    loadProjectDetails,
    getAssetContent,
    updateAssetContent,
  };
}
