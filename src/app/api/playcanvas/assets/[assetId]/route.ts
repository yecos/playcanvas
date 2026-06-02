import { NextRequest, NextResponse } from 'next/server';
import { PlayCanvasClient } from '@/lib/playcanvas-api';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ assetId: string }> }
) {
  try {
    const { assetId } = await params;
    const authToken = request.headers.get('x-playcanvas-token');
    if (!authToken) {
      return NextResponse.json({ error: 'Missing PlayCanvas API token' }, { status: 401 });
    }

    const client = new PlayCanvasClient(authToken);
    const aId = parseInt(assetId);
    
    // First get the asset details to find the file URL (which includes branchId)
    const asset = await client.getAsset(aId);
    
    if (!asset.file?.url) {
      return NextResponse.json({ error: 'Asset has no file URL', asset }, { status: 404 });
    }

    // Use the file URL from the asset (it already includes the branchId)
    const fileContent = await client.getAssetFileByUrl(asset.file.url);
    
    return NextResponse.json({ content: fileContent, asset: { id: asset.id, name: asset.name, type: asset.type } });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ assetId: string }> }
) {
  try {
    const { assetId } = await params;
    const authToken = request.headers.get('x-playcanvas-token');
    if (!authToken) {
      return NextResponse.json({ error: 'Missing PlayCanvas API token' }, { status: 401 });
    }

    const client = new PlayCanvasClient(authToken);
    const aId = parseInt(assetId);
    const body = await request.json();
    const { content } = body;

    // First get asset details to find branchId from file URL
    const asset = await client.getAsset(aId);
    
    // Extract branchId from the file URL
    let branchId: string | undefined;
    if (asset.file?.url) {
      const match = asset.file.url.match(/branchId=([^&]+)/);
      if (match) branchId = match[1];
    }

    const blob = new Blob([content], { type: 'text/javascript' });
    const result = await client.updateAssetFile(aId, blob, branchId);
    
    return NextResponse.json({ success: true, asset: result });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
