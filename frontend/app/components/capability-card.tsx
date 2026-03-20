'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useAgentCapabilities } from '@/hooks/use-agent-capabilities';
import { Brain, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function CapabilityGrid() {
  const { data, isLoading, isError, error, refetch } = useAgentCapabilities();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card key={i} className="border-border/40">
            <CardHeader className="pb-2">
              <Skeleton className="h-5 w-32" />
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="flex flex-wrap gap-1">
                {Array.from({ length: 3 }).map((_, j) => (
                  <Skeleton key={j} className="h-5 w-20 rounded-full" />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center gap-3 text-muted-foreground">
        <AlertCircle className="w-10 h-10 text-destructive/70" />
        <p className="font-medium">Failed to load agent capabilities</p>
        <p className="text-sm">{error?.message}</p>
        <Button variant="outline" size="sm" onClick={() => refetch()} className="gap-2 mt-1">
          <RefreshCw className="w-4 h-4" />
          Retry
        </Button>
      </div>
    );
  }

  const agents = data?.agents ?? [];

  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center gap-3 text-muted-foreground">
        <Brain className="w-10 h-10 opacity-40" />
        <p className="font-medium">No agents available</p>
        <p className="text-sm">Agents will appear here once the backend is running.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {agents.length} agent{agents.length !== 1 ? 's' : ''} available
        </p>
        <Button variant="ghost" size="sm" onClick={() => refetch()} className="gap-2 text-muted-foreground">
          <RefreshCw className="w-3 h-3" />
          Refresh
        </Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents.map(agent => (
          <CapabilityCard key={agent.name} agent={agent} />
        ))}
      </div>
    </div>
  );
}

function CapabilityCard({ agent }: { agent: { name: string; capabilities: string[]; description?: string } }) {
  return (
    <Card className="border-border/40 bg-card/50 hover:bg-card/80 transition-colors group">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold capitalize">
          <Brain className="w-4 h-4 text-primary flex-shrink-0" />
          {agent.name.replace(/_/g, ' ')}
        </CardTitle>
        {agent.description && (
          <p className="text-xs text-muted-foreground leading-relaxed">{agent.description}</p>
        )}
      </CardHeader>
      <CardContent>
        {agent.capabilities.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {agent.capabilities.map(cap => (
              <Badge
                key={cap}
                variant="secondary"
                className="text-xs bg-primary/10 text-primary border-primary/20 hover:bg-primary/20 transition-colors"
              >
                {cap}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-xs text-muted-foreground italic">No capabilities listed</p>
        )}
      </CardContent>
    </Card>
  );
}
