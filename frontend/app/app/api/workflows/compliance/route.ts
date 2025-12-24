
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { uploadFile } from '@/lib/s3';
import { createApiClient } from '@/lib/api-client';
import type { paths } from '@/lib/api-types';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
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

    const formData = await request.formData();
    const query = formData.get('query') as string;
    const file = formData.get('file') as File | null;
    const parameters = formData.get('parameters') as string;
    const jurisdiction = formData.get('jurisdiction') as string | null;
    const riskThreshold = formData.get('risk_threshold') as string | null;

    let documentPath = null;
    
    if (file) {
      const buffer = Buffer.from(await file.arrayBuffer());
      documentPath = await uploadFile(buffer, file.name);
    }

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (session.accessToken) {
      headers.Authorization = `Bearer ${session.accessToken}`;
    }
    const apiKey = request.headers.get('x-api-key');
    if (apiKey) {
      headers['X-API-Key'] = apiKey;
    }

    type ComplianceRequest =
      paths['/api/v1/workflows/compliance']['post']['requestBody']['content']['application/json'];
    const parsedRisk = riskThreshold ? Number(riskThreshold) : 0.7;
    const payload: ComplianceRequest = {
      query,
      risk_threshold: Number.isNaN(parsedRisk) ? 0.7 : parsedRisk,
    };
    if (jurisdiction) {
      payload.jurisdiction = jurisdiction;
    }
    if (parameters) {
      payload.config = JSON.parse(parameters);
    }
    if (documentPath) {
      payload.policy_documents = [documentPath];
    }

    // Call FastAPI backend
    const client = createApiClient(backendUrl);
    const { data, response } = await client.POST('/api/v1/workflows/compliance', {
      body: payload,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to start workflow: ${response.status} ${errorText}`);
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error('Workflow start error:', error);
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
