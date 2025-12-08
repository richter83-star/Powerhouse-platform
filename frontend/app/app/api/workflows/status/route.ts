
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { prisma } from '@/lib/db';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const workflowId = searchParams.get('workflowId');

    if (!workflowId) {
      return NextResponse.json({ error: 'Workflow ID required' }, { status: 400 });
    }

    // Call FastAPI backend
    const backendResponse = await fetch(
      `http://localhost:8001/api/v1/workflows/${workflowId}/status`
    );

    if (!backendResponse.ok) {
      throw new Error('Failed to get workflow status');
    }

    const statusData = await backendResponse.json();

    // Update workflow status in database
    await prisma.workflow.update({
      where: { workflowId },
      data: { 
        status: statusData.status,
        updatedAt: new Date(),
      },
    });

    return NextResponse.json(statusData, { status: 200 });
  } catch (error: any) {
    console.error('Workflow status error:', error);
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
