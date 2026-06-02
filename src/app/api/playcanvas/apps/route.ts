import { NextRequest, NextResponse } from 'next/server';
import { PlayCanvasClient } from '@/lib/playcanvas-api';

export async function GET(request: NextRequest) {
  try {
    const authToken = request.headers.get('x-playcanvas-token');
    if (!authToken) {
      return NextResponse.json({ error: 'Missing PlayCanvas API token' }, { status: 401 });
    }

    const client = new PlayCanvasClient(authToken);
    const apps = await client.listApps();

    return NextResponse.json({ apps });
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
