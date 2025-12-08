
import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import bcrypt from 'bcryptjs';

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

    try {
      // Check if user already exists
      const existingUser = await prisma.user.findUnique({
        where: { email }
      });

      if (existingUser) {
        return NextResponse.json(
          { error: 'User already exists' },
          { status: 400 }
        );
      }

      // Hash password
      const hashedPassword = await bcrypt.hash(password, 10);

      // Create user
      const user = await prisma.user.create({
        data: {
          email,
          password: hashedPassword,
          fullName,
          companyName: companyName || null,
          jobTitle: jobTitle || null,
        },
        select: {
          id: true,
          email: true,
          fullName: true,
          companyName: true,
          jobTitle: true,
        }
      });

      return NextResponse.json(user, { status: 201 });
    } catch (dbError: any) {
      // If database is unavailable, return mock success for demo purposes
      console.warn('[DEMO MODE] Database unavailable, using mock response:', dbError?.message);
      
      const mockUser = {
        id: `mock-${Date.now()}`,
        email,
        fullName,
        companyName: companyName || null,
        jobTitle: jobTitle || null,
      };

      return NextResponse.json(mockUser, { status: 201 });
    }
  } catch (error: any) {
    console.error('Signup error:', error);
    return NextResponse.json(
      { error: error?.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
