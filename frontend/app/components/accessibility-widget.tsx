
'use client';

import React, { useState } from 'react';
import { Eye, EyeOff, Type, Contrast, Volume2, VolumeX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { usePreferences } from '@/contexts/preferences-context';

export function AccessibilityWidget() {
  const { preferences, updatePreferences } = usePreferences();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed bottom-4 right-4 z-50 no-print">
      <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
        <DropdownMenuTrigger asChild>
          <Button
            size="lg"
            className="rounded-full shadow-lg h-14 w-14"
            aria-label="Accessibility Options"
          >
            <Eye className="h-6 w-6" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-64">
          <DropdownMenuLabel>Accessibility Options</DropdownMenuLabel>
          <DropdownMenuSeparator />
          
          <DropdownMenuItem
            onClick={() => updatePreferences({ 
              fontSize: preferences.fontSize === 'large' ? 'medium' : 'large' 
            })}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <Type className="h-4 w-4" />
              Large Text
            </span>
            {preferences.fontSize === 'large' && (
              <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">ON</span>
            )}
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => updatePreferences({ 
              highContrast: !preferences.highContrast 
            })}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="flex items-center gap-2">
              <Contrast className="h-4 w-4" />
              High Contrast
            </span>
            {preferences.highContrast && (
              <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">ON</span>
            )}
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => updatePreferences({ 
              reducedMotion: !preferences.reducedMotion 
            })}
            className="flex items-center justify-between cursor-pointer"
          >
            <span className="flex items-center gap-2">
              {preferences.reducedMotion ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              Reduce Motion
            </span>
            {preferences.reducedMotion && (
              <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">ON</span>
            )}
          </DropdownMenuItem>

          <DropdownMenuSeparator />
          
          <DropdownMenuItem asChild>
            <a 
              href="/settings" 
              className="cursor-pointer"
            >
              More Settings →
            </a>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
