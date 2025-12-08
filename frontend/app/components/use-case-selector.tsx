
'use client';

import { useUseCase } from '@/contexts/use-case-context';
import { USE_CASES } from '@/lib/use-cases';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Shield, 
  Headphones, 
  TrendingUp, 
  Search, 
  Sparkles,
  Network
} from 'lucide-react';

const iconMap: Record<string, any> = {
  Shield,
  Headphones,
  TrendingUp,
  Search,
  Sparkles,
  Network
};

export function UseCaseSelector() {
  const { currentUseCase, setUseCase } = useUseCase();

  const getIcon = (iconName: string) => {
    const IconComponent = iconMap[iconName];
    return IconComponent ? <IconComponent className="w-4 h-4" /> : null;
  };

  return (
    <Select value={currentUseCase.id} onValueChange={setUseCase}>
      <SelectTrigger className="w-[280px] bg-white/90 backdrop-blur-sm border-slate-200">
        <div className="flex items-center gap-2">
          {getIcon(currentUseCase.icon)}
          <SelectValue />
        </div>
      </SelectTrigger>
      <SelectContent>
        {USE_CASES.map((useCase) => (
          <SelectItem key={useCase.id} value={useCase.id}>
            <div className="flex items-center gap-2">
              {getIcon(useCase.icon)}
              <span>{useCase.name}</span>
            </div>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
