
'use client';

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Workflow } from '@/lib/types';
import { Clock, CheckCircle, XCircle, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface WorkflowCardProps {
  workflow: Workflow;
}

export function WorkflowCard({ workflow }: WorkflowCardProps) {
  const statusIcon = {
    pending: <Clock className="w-4 h-4 text-yellow-500" />,
    running: <Clock className="w-4 h-4 text-blue-500 animate-spin" />,
    completed: <CheckCircle className="w-4 h-4 text-green-500" />,
    failed: <XCircle className="w-4 h-4 text-red-500" />,
  };

  const statusColor = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <Card className="p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            {statusIcon?.[workflow?.status as keyof typeof statusIcon] || statusIcon.pending}
            <Badge className={statusColor?.[workflow?.status as keyof typeof statusColor] || statusColor.pending}>
              {workflow?.status || 'unknown'}
            </Badge>
          </div>
          <h3 className="font-semibold text-gray-900">
            Workflow {workflow?.workflowId?.substring(0, 8) || 'Unknown'}
          </h3>
        </div>
        <p className="text-sm text-gray-500">
          {workflow?.createdAt ? new Date(workflow.createdAt).toLocaleDateString() : 'N/A'}
        </p>
      </div>
      
      {workflow?.query && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
          {workflow.query}
        </p>
      )}
      
      <div className="flex gap-2">
        {workflow?.status === 'running' && (
          <Link href={`/workflows/${workflow.workflowId}`} className="flex-1">
            <Button variant="outline" size="sm" className="w-full">
              View Status
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        )}
        {workflow?.status === 'completed' && (
          <Link href={`/results/${workflow.workflowId}`} className="flex-1">
            <Button size="sm" className="w-full">
              View Results
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </Link>
        )}
      </div>
    </Card>
  );
}
