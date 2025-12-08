
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const agentId = searchParams.get('agentId');

    if (!agentId) {
      return NextResponse.json({ error: 'Agent ID required' }, { status: 400 });
    }

    // Call FastAPI backend
    const backendResponse = await fetch(
      `http://localhost:8001/api/v1/agents/${agentId}/status`
    );

    if (!backendResponse.ok) {
      throw new Error('Failed to get agent status');
    }

    const statusData = await backendResponse.json();

    return NextResponse.json(statusData, { status: 200 });
  } catch (error: any) {
    console.error('Agent status error:', error);
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
