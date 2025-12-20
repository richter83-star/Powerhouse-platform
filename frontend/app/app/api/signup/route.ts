
import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password, fullName, companyName, jobTitle } = body;

    if (!email || !password || !fullName) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Use backend API for signup (bypasses Prisma issues)
    // Use internal URL when running in Docker, external URL for client-side
    const backendUrl = process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    
    try {
      const response = await fetch(`${backendUrl}/api/auth/signup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.toLowerCase().trim(),
          password: password,
          full_name: fullName,
          company_name: companyName || null,
          job_title: jobTitle || null,
          tenant_id: 'default', // Default tenant for now
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        return NextResponse.json(
          { error: data.detail || data.message || 'Signup failed' },
          { status: response.status }
        );
      }

      // Return user info for frontend
      return NextResponse.json({
        id: data.user_id,
        email: email,
        fullName: fullName,
        companyName: companyName || null,
        jobTitle: jobTitle || null,
        message: data.message,
      }, { status: 201 });
    } catch (backendError: any) {
      console.error('Backend signup error:', backendError);
      return NextResponse.json(
        { error: 'Failed to connect to backend. Please ensure the backend is running.' },
        { status: 503 }
      );
    }
  } catch (error: any) {
    console.error('Signup error:', error);
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
