
import { NextRequest, NextResponse } from 'next/server';
import { createApiClient } from '@/lib/api-client';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    // Call FastAPI backend
    // Use internal URL when running in Docker, external URL for client-side
    const backendUrl = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers.Authorization = authHeader;
    }
    const apiKey = request.headers.get('x-api-key');
    if (apiKey) {
      headers['X-API-Key'] = apiKey;
    }

    const client = createApiClient(backendUrl);
    const { data, response } = await client.GET('/api/v1/agents', {
      headers,
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', errorText);
      throw new Error(`Failed to get agents: ${response.status} ${errorText}`);
    }

    return NextResponse.json(data, { status: response.status });
  } catch (error: any) {
    console.error('Agents fetch error:', error);
    console.error('Error details:', {
      message: error?.message,
      cause: error?.cause,
      stack: error?.stack,
    });
    return NextResponse.json(
      { 
        error: error?.message || 'Internal server error',
        details: error?.cause?.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
}
