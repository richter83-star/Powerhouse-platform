
'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter, useParams } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { WorkflowStatus } from '@/lib/types';
import { 
  Activity, 
  CheckCircle, 
  Clock, 
  XCircle,
  ArrowRight,
  RefreshCw
} from 'lucide-react';
import Link from 'next/link';

export default function WorkflowStatusPage() {
  const { data: session, status } = useSession() || {};
  const router = useRouter();
  const params = useParams();
  const workflowId = params?.id as string;

  const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  useEffect(() => {
    if (status === 'authenticated' && workflowId) {
      fetchStatus();
      // Poll for status updates every 3 seconds
      const interval = setInterval(fetchStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [status, workflowId]);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`/api/workflows/status?workflowId=${workflowId}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch workflow status');
      }

      const data = await response.json();
      setWorkflowStatus(data);
      setError('');

      // If completed, stop polling
      if (data?.status === 'completed' || data?.status === 'failed') {
        // Optional: Auto-redirect to results page after completion
        // setTimeout(() => router.push(`/results/${workflowId}`), 2000);
      }
    } catch (err: any) {
      console.error('Status fetch error:', err);
      setError(err?.message || 'Failed to fetch status');
    } finally {
      setLoading(false);
    }
  };

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (status === 'unauthenticated') {
    return null;
  }

  const statusIcon = {
    pending: <Clock className="w-6 h-6 text-yellow-500" />,
    running: <Activity className="w-6 h-6 text-blue-500 animate-pulse" />,
    completed: <CheckCircle className="w-6 h-6 text-green-500" />,
    failed: <XCircle className="w-6 h-6 text-red-500" />,
  };

  const statusColor = {
    pending: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  const currentStatus = workflowStatus?.status || 'pending';

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            {statusIcon?.[currentStatus as keyof typeof statusIcon]}
            <h1 className="text-3xl font-bold text-gray-900">
              Workflow Status
            </h1>
            <Badge className={statusColor?.[currentStatus as keyof typeof statusColor]}>
              {currentStatus}
            </Badge>
          </div>
          <p className="text-gray-600">
            Workflow ID: <span className="font-mono text-sm">{workflowId}</span>
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-8 bg-red-50 border-red-200">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-sm font-semibold text-red-800">Error</h4>
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Overall Progress */}
        {workflowStatus && (
          <>
            <Card className="mb-8">
              <CardHeader>
                <CardTitle>Overall Progress</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Progress value={workflowStatus?.progress || 0} className="h-3" />
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">
                      {workflowStatus?.currentStep || 'Initializing...'}
                    </span>
                    <span className="font-semibold text-gray-900">
                      {workflowStatus?.progress || 0}%
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Agent Statuses */}
            {workflowStatus?.agentStatuses && workflowStatus.agentStatuses.length > 0 && (
              <Card className="mb-8">
                <CardHeader>
                  <CardTitle>Agent Activity</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {workflowStatus.agentStatuses.map((agent, index) => (
                      <div key={agent?.agentId || index} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                              <Activity className="w-5 h-5 text-blue-600" />
                            </div>
                            <div>
                              <h4 className="font-semibold text-gray-900">
                                {agent?.agentName || 'Unknown Agent'}
                              </h4>
                              <p className="text-sm text-gray-500">{agent?.status || 'idle'}</p>
                            </div>
                          </div>
                          <span className="text-sm font-semibold text-gray-900">
                            {agent?.progress || 0}%
                          </span>
                        </div>
                        <Progress value={agent?.progress || 0} className="h-2" />
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Actions */}
            <div className="flex gap-4">
              {currentStatus === 'completed' && (
                <Link href={`/results/${workflowId}`} className="flex-1">
                  <Button className="w-full" size="lg">
                    View Results
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </Link>
              )}
              
              <Button
                variant="outline"
                size="lg"
                onClick={fetchStatus}
                disabled={currentStatus === 'completed' || currentStatus === 'failed'}
              >
                <RefreshCw className="w-5 h-5 mr-2" />
                Refresh
              </Button>

              <Link href="/dashboard">
                <Button variant="ghost" size="lg">
                  Back to Dashboard
                </Button>
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
