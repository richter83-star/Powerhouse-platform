
'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  text?: string;
  fullScreen?: boolean;
  className?: string;
}

export function LoadingState({ 
  size = 'md', 
  text = 'Loading...', 
  fullScreen = false,
  className 
}: LoadingStateProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
  };

  const content = (
    <div className={cn(
      'flex flex-col items-center justify-center gap-4',
      fullScreen && 'min-h-screen',
      className
    )}>
      <Loader2 className={cn(
        sizeClasses[size],
        'animate-spin text-primary'
      )} />
      {text && (
        <p className={cn(
          textSizeClasses[size],
          'text-muted-foreground font-medium'
        )}>
          {text}
        </p>
      )}
    </div>
  );

  return content;
}

export function LoadingOverlay({ show }: { show: boolean }) {
  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <LoadingState size="lg" text="Processing..." />
    </div>
  );
}

export function LoadingSkeleton({ 
  rows = 3,
  className 
}: { 
  rows?: number;
  className?: string;
}) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-12 bg-muted animate-pulse rounded-lg"
          style={{
            animationDelay: `${i * 0.1}s`,
          }}
        />
      ))}
    </div>
  );
}
