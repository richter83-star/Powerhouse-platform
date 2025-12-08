
'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Agent } from '@/lib/types';
import { Bot, CheckCircle, XCircle, Clock } from 'lucide-react';

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const statusIcon = {
    idle: <CheckCircle className="w-4 h-4 text-green-500" />,
    running: <Clock className="w-4 h-4 text-yellow-500" />,
    completed: <CheckCircle className="w-4 h-4 text-blue-500" />,
    failed: <XCircle className="w-4 h-4 text-red-500" />,
  };

  const statusColor = {
    idle: 'bg-green-100 text-green-800',
    running: 'bg-yellow-100 text-yellow-800',
    completed: 'bg-blue-100 text-blue-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-100 rounded-lg">
            <Bot className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-lg text-gray-900">{agent?.name || 'Unknown Agent'}</h3>
            <p className="text-sm text-gray-500">{agent?.type || 'Unknown Type'}</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {statusIcon?.[agent?.status || 'idle']}
          <Badge className={statusColor?.[agent?.status || 'idle']}>
            {agent?.status || 'idle'}
          </Badge>
        </div>
      </div>
      
      <p className="text-sm text-gray-600 mb-4">
        {agent?.description || 'No description available'}
      </p>
      
      {agent?.capabilities && agent.capabilities.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {agent.capabilities.map((capability, index) => (
            <Badge key={index} variant="outline" className="text-xs">
              {capability}
            </Badge>
          ))}
        </div>
      )}
    </Card>
  );
}
