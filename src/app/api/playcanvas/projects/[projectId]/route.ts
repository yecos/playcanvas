import { NextRequest, NextResponse } from 'next/server';
import { PlayCanvasClient } from '@/lib/playcanvas-api';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ projectId: string }> }
) {
  try {
    const { projectId } = await params;
    const authToken = request.headers.get('x-playcanvas-token');
    if (!authToken) {
      return NextResponse.json({ error: 'Missing PlayCanvas API token' }, { status: 401 });
    }

    const client = new PlayCanvasClient(authToken);
    const pId = parseInt(projectId);
    
    const [scenesResult, assetsResult] = await Promise.allSettled([
      client.listScenes(pId),
      client.listAssets(pId),
    ]);

    const scenes = scenesResult.status === 'fulfilled' ? scenesResult.value : [];
    const assetsData = assetsResult.status === 'fulfilled' ? assetsResult.value : { result: [], pagination: { skip: 0, limit: 0, total: 0 } };

    const assetsByType: Record<string, number> = {};
    const assetsByName: Record<string, PlayCanvasAsset[]> = {};
    assetsData.result.forEach((a: { type: string; name: string }) => {
      assetsByType[a.type] = (assetsByType[a.type] || 0) + 1;
      if (!assetsByName[a.name]) assetsByName[a.name] = [];
      assetsByName[a.name].push(a);
    });

    return NextResponse.json({
      projectId: pId,
      scenes,
      assets: {
        total: assetsData.pagination.total,
        byType: assetsByType,
        items: assetsData.result,
      },
    });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
