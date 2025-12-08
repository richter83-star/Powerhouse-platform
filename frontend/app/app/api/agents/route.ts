
import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    // Call FastAPI backend
    const backendResponse = await fetch('http://localhost:8001/api/v1/agents', {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.error('Backend error:', errorText);
      throw new Error(`Failed to get agents: ${backendResponse.status} ${errorText}`);
    }

    const agentsData = await backendResponse.json();

    return NextResponse.json(agentsData, { status: 200 });
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
