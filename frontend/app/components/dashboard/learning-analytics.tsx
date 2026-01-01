'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Brain,
  TrendingUp,
  RefreshCw,
  BookOpen,
  Award
} from 'lucide-react';

interface LearningMetrics {
  total_updates: number;
  successful_updates: number;
  failed_updates: number;
  avg_update_time_ms: number;
  samples_processed: number;
  current_model_score: number;
  improvement_rate: number;
}

interface AgentPerformance {
  agent_name: string;
  success_rate: number;
  avg_latency_ms: number;
  total_executions: number;
}

interface ModelInfo {
  model_type: string;
  update_count: number;
  last_update: string;
  performance_summary: {
    total_agents: number;
    task_patterns: number;
  };
}

export function LearningAnalytics() {
  const [metrics, setMetrics] = useState<LearningMetrics | null>(null);
  const [agentPerformance, setAgentPerformance] = useState<AgentPerformance[]>([]);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [statusInfo, setStatusInfo] = useState<{ status?: string; running?: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLearning = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const results = await Promise.allSettled([
          fetch(`${apiUrl}/api/learning/metrics`),
          fetch(`${apiUrl}/api/learning/agents/performance`),
          fetch(`${apiUrl}/api/learning/models/agent_selection`),
          fetch(`${apiUrl}/api/learning/status`)
        ]);

        const metricsRes = results[0].status === 'fulfilled' ? results[0].value : null;
        const agentsRes = results[1].status === 'fulfilled' ? results[1].value : null;
        const modelRes = results[2].status === 'fulfilled' ? results[2].value : null;
        const statusRes = results[3].status === 'fulfilled' ? results[3].value : null;

        if (metricsRes?.ok) {
          const data = await metricsRes.json();
          setMetrics(data);
        }

        if (agentsRes?.ok) {
          const data = await agentsRes.json();
          setAgentPerformance(Array.isArray(data) ? data : []);
        }

        if (modelRes?.ok) {
          const data = await modelRes.json();
          setModelInfo(data);
        }

        if (statusRes?.ok) {
          const data = await statusRes.json();
          setStatusInfo(data);
        }
      } catch (error) {
        console.error('Failed to fetch learning analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchLearning();
  }, []);

  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '--';
    }
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatLatency = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '--';
    }
    if (value >= 1000) {
      return `${(value / 1000).toFixed(2)}s`;
    }
    return `${Math.round(value)}ms`;
  };

  const statusLabel = statusInfo?.status || 'unknown';
  const statusBadge = statusLabel === 'running'
    ? 'bg-green-100 text-green-700 border-0'
    : statusLabel === 'stopped'
      ? 'bg-yellow-100 text-yellow-700 border-0'
      : 'bg-slate-100 text-slate-700 border-0';

  return (
    <div className="space-y-6">
      {/* Learning Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Brain className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Score</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Model Score</p>
            <p className="text-4xl font-bold">{metrics ? formatPercent(metrics.current_model_score) : '--'}</p>
            <p className="text-xs opacity-75 mt-2">Online learning quality</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <TrendingUp className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Growth</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Improvement Rate</p>
            <p className="text-4xl font-bold">{metrics ? formatPercent(metrics.improvement_rate) : '--'}</p>
            <p className="text-xs opacity-75 mt-2">Rolling accuracy uplift</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <RefreshCw className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Updates</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Model Updates</p>
            <p className="text-4xl font-bold">{metrics ? metrics.total_updates : '--'}</p>
            <p className="text-xs opacity-75 mt-2">Successful: {metrics ? metrics.successful_updates : '--'}</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <BookOpen className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Data</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Samples Processed</p>
            <p className="text-4xl font-bold">{metrics ? metrics.samples_processed.toLocaleString() : '--'}</p>
            <p className="text-xs opacity-75 mt-2">Pipeline ingest</p>
          </CardContent>
        </Card>
      </div>

      {/* Agent Performance */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Agent Performance Snapshot
          </CardTitle>
          <CardDescription>Success rate and latency from the online learning model</CardDescription>
        </CardHeader>
        <CardContent>
          {agentPerformance.length === 0 ? (
            <div className="text-sm text-slate-600">
              {loading ? 'Loading agent performance...' : 'No agent performance data available.'}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={agentPerformance}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="agent_name" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #e2e8f0',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                  }}
                />
                <Legend />
                <Bar dataKey="success_rate" fill="#10b981" name="Success Rate" />
                <Bar dataKey="avg_latency_ms" fill="#3b82f6" name="Avg Latency (ms)" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Model Update Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5 text-purple-600" />
              Model Update Summary
            </CardTitle>
            <CardDescription>Online learning model metadata and update cadence</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {modelInfo ? (
              <>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Model Type</span>
                  <span className="font-semibold text-slate-900">{modelInfo.model_type}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Update Count</span>
                  <span className="font-semibold text-slate-900">{modelInfo.update_count}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Last Update</span>
                  <span className="font-semibold text-slate-900">{modelInfo.last_update || '--'}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Agents Tracked</span>
                  <span className="font-semibold text-slate-900">{modelInfo.performance_summary.total_agents}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">Task Patterns</span>
                  <span className="font-semibold text-slate-900">{modelInfo.performance_summary.task_patterns}</span>
                </div>
              </>
            ) : (
              <p className="text-sm text-slate-600">
                Model metadata is not available yet.
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-green-600" />
              Learning Service Status
            </CardTitle>
            <CardDescription>Online learning pipeline connectivity</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Status</span>
              <Badge className={statusBadge}>{statusLabel}</Badge>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Running</span>
              <span className="font-semibold text-slate-900">{statusInfo?.running ? 'Yes' : 'No'}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Avg Update Time</span>
              <span className="font-semibold text-slate-900">{metrics ? formatLatency(metrics.avg_update_time_ms) : '--'}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-600">Failed Updates</span>
              <span className="font-semibold text-slate-900">{metrics ? metrics.failed_updates : '--'}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
