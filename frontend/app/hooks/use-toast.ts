
// Toast hook with backwards compatibility
import { useToast as useNewToast } from '@/components/toast-provider';

export interface ToastOptions {
  title: string;
  description?: string;
  variant?: 'default' | 'destructive' | 'success';
  duration?: number;
}

export function useToast() {
  const { success, error, info, addToast } = useNewToast();

  const toast = (options: ToastOptions) => {
    const { title, description, variant = 'default', duration } = options;
    
    if (variant === 'destructive') {
      error(title, description);
    } else if (variant === 'success') {
      success(title, description);
    } else {
      info(title, description);
    }
  };

  return { 
    toast,
    success,
    error,
    info,
    warning: info
  };
}
