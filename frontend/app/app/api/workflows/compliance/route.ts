
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { uploadFile } from '@/lib/s3';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const formData = await request.formData();
    const query = formData.get('query') as string;
    const file = formData.get('file') as File | null;
    const parameters = formData.get('parameters') as string;

    let documentPath = null;
    
    if (file) {
      const buffer = Buffer.from(await file.arrayBuffer());
      documentPath = await uploadFile(buffer, file.name);
    }

    // Call FastAPI backend
    const backendResponse = await fetch('http://localhost:8001/api/v1/workflows/compliance', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        document: documentPath,
        parameters: parameters ? JSON.parse(parameters) : {},
      }),
    });

    if (!backendResponse.ok) {
      throw new Error('Failed to start workflow');
    }

    const workflowData = await backendResponse.json();

    // Save workflow to database
    const workflow = await prisma.workflow.create({
      data: {
        userId: (session.user as any).id,
        workflowId: workflowData.workflow_id,
        status: 'pending',
        query,
        documentPath,
        parameters: parameters ? JSON.parse(parameters) : {},
      },
    });

    return NextResponse.json({
      workflowId: workflow.workflowId,
      status: workflow.status,
    }, { status: 200 });
  } catch (error: any) {
    console.error('Workflow start error:', error);
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
