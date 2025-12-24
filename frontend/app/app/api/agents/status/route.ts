
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { createApiClient } from '@/lib/api-client';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const backendUrl =
      process.env.BACKEND_INTERNAL_URL ||
      process.env.NEXT_PUBLIC_BACKEND_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      'http://localhost:8001';

    const { searchParams } = new URL(request.url);
    const agentId = searchParams.get('agentId');

    if (!agentId) {
      return NextResponse.json({ error: 'Agent ID required' }, { status: 400 });
    }

    // Call FastAPI backend
    const headers: Record<string, string> = {};
    if (session.accessToken) {
      headers.Authorization = `Bearer ${session.accessToken}`;
    }
    const apiKey = request.headers.get('x-api-key');
    if (apiKey) {
      headers['X-API-Key'] = apiKey;
    }

    const client = createApiClient(backendUrl);
    const { data, response } = await client.GET(
      '/api/v1/agents/{agent_id}/status',
      {
        params: { path: { agent_id: agentId } },
        headers,
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to get agent status: ${response.status} ${errorText}`);
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error('Agent status error:', error);
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
