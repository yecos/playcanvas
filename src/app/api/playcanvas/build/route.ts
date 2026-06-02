import { NextRequest, NextResponse } from 'next/server';
import { PlayCanvasClient } from '@/lib/playcanvas-api';

export async function POST(request: NextRequest) {
  try {
    const authToken = request.headers.get('x-playcanvas-token');
    if (!authToken) {
      return NextResponse.json({ error: 'Missing PlayCanvas API token' }, { status: 401 });
    }

    const body = await request.json();
    const { projectId, name, scenes, branchId, format } = body;

    const client = new PlayCanvasClient(authToken);
    const jobId = await client.downloadBuild({
      projectId,
      name,
      scenes,
      branchId,
      format: format || 'npm',
    });

    return NextResponse.json({ jobId, status: 'started' });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
