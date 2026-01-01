'use client';

import { useEffect, useMemo, useState } from 'react';
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
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  TrendingUp,
  CheckCircle2,
  Activity,
  Zap
} from 'lucide-react';

interface SystemMetrics {
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  partial_tasks: number;
  success_rate: number;
  avg_latency_ms: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  max_latency_ms: number;
  total_tokens: number;
  total_api_calls: number;
  total_cost: number;
  avg_accuracy: number;
  avg_quality_score: number;
}

interface AgentMetric {
  model: string;
  accuracy: number;
  latency: number;
  throughput: number;
}

export function PerformanceMetrics() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics | null>(null);
  const [agentMetrics, setAgentMetrics] = useState<AgentMetric[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const results = await Promise.allSettled([
          fetch(`${apiUrl}/api/performance/metrics/system?time_window_minutes=60`),
          fetch(`${apiUrl}/api/performance/metrics/agents?time_window_minutes=60`)
        ]);

        const systemRes = results[0].status === 'fulfilled' ? results[0].value : null;
        const agentsRes = results[1].status === 'fulfilled' ? results[1].value : null;

        if (systemRes?.ok) {
          const data = await systemRes.json();
          setSystemMetrics(data?.metrics || null);
        }

        if (agentsRes?.ok) {
          const data = await agentsRes.json();
          const agents = data?.agents || {};
          const rows: AgentMetric[] = Object.entries(agents).map(([name, detail]: any) => ({
            model: name,
            accuracy: (detail?.metrics?.success_rate ?? 0) * 100,
            latency: detail?.metrics?.avg_latency_ms ?? 0,
            throughput: detail?.metrics?.total_tasks ?? 0
          }));
          setAgentMetrics(rows);
        }
      } catch (error) {
        console.error('Failed to fetch performance metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  const formatNumber = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '--';
    }
    return value.toLocaleString();
  };

  const formatPercent = (value: number | null | undefined) => {
    if (value === null || value === undefined || Number.isNaN(value)) {
      return '--';
    }
    return `${value.toFixed(1)}%`;
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

  const throughputPerHour = systemMetrics?.total_tasks ?? 0;
  const accuracyValue = systemMetrics?.avg_accuracy && systemMetrics.avg_accuracy > 0
    ? systemMetrics.avg_accuracy * 100
    : (systemMetrics?.avg_quality_score ?? 0) * 100;

  const latencyPercentiles = useMemo(() => {
    if (!systemMetrics) {
      return [];
    }
    return [
      { name: 'P50', value: systemMetrics.p50_latency_ms },
      { name: 'P95', value: systemMetrics.p95_latency_ms },
      { name: 'P99', value: systemMetrics.p99_latency_ms },
      { name: 'Max', value: systemMetrics.max_latency_ms }
    ];
  }, [systemMetrics]);

  const taskDistribution = useMemo(() => {
    if (!systemMetrics) {
      return [];
    }
    return [
      { name: 'Successful', value: systemMetrics.successful_tasks, color: '#10b981' },
      { name: 'Failed', value: systemMetrics.failed_tasks, color: '#ef4444' },
      { name: 'Partial', value: systemMetrics.partial_tasks, color: '#f59e0b' }
    ];
  }, [systemMetrics]);

  const totalTasks = systemMetrics?.total_tasks ?? 0;
  const avgCostPerTask = totalTasks > 0
    ? (systemMetrics?.total_cost ?? 0) / totalTasks
    : 0;

  return (
    <div className="space-y-6">
      {/* Real-time Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Activity className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Last 60m</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Average Latency</p>
            <p className="text-4xl font-bold">
              {systemMetrics ? formatLatency(systemMetrics.avg_latency_ms) : '--'}
            </p>
            <p className="text-xs opacity-75 mt-2">
              {loading ? 'Loading metrics...' : 'Rolling window'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Zap className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Last 60m</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Throughput</p>
            <p className="text-4xl font-bold">{formatNumber(throughputPerHour)}</p>
            <p className="text-xs opacity-75 mt-2">tasks/hr</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <CheckCircle2 className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Last 60m</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Success Rate</p>
            <p className="text-4xl font-bold">
              {systemMetrics ? formatPercent(systemMetrics.success_rate * 100) : '--'}
            </p>
            <p className="text-xs opacity-75 mt-2">based on completed tasks</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <TrendingUp className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Last 60m</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Accuracy</p>
            <p className="text-4xl font-bold">
              {systemMetrics ? formatPercent(accuracyValue) : '--'}
            </p>
            <p className="text-xs opacity-75 mt-2">reported accuracy score</p>
          </CardContent>
        </Card>
      </div>

      {/* Latency Percentiles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle>Latency Percentiles</CardTitle>
            <CardDescription>Distribution of response latency in the last hour</CardDescription>
          </CardHeader>
          <CardContent>
            {latencyPercentiles.length === 0 ? (
              <div className="text-sm text-slate-600">No latency data available yet.</div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={latencyPercentiles}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" stroke="#64748b" />
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
                  <Bar dataKey="value" fill="#3b82f6" name="Latency (ms)" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle>Task Outcomes</CardTitle>
            <CardDescription>Success vs failure breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {taskDistribution.length === 0 || totalTasks === 0 ? (
              <div className="text-sm text-slate-600">No task outcomes reported yet.</div>
            ) : (
              <>
                <div className="flex items-center justify-center">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={taskDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
                        outerRadius={100}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {taskDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-6">
                  {taskDistribution.map((item, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                      <span className="text-sm font-medium text-slate-700">{item.name}</span>
                      <span className="text-sm font-bold text-slate-900 ml-auto">{item.value}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Model-specific Metrics */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle>Agent Model Performance</CardTitle>
          <CardDescription>Per-agent success rate, latency, and throughput</CardDescription>
        </CardHeader>
        <CardContent>
          {agentMetrics.length === 0 ? (
            <div className="text-sm text-slate-600">No agent metrics available yet.</div>
          ) : (
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={agentMetrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="model" stroke="#64748b" />
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
                <Bar dataKey="accuracy" fill="#10b981" name="Success Rate (%)" />
                <Bar dataKey="latency" fill="#3b82f6" name="Avg Latency (ms)" />
                <Bar dataKey="throughput" fill="#f59e0b" name="Tasks" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Cost Summary */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle>Cost Summary</CardTitle>
          <CardDescription>Aggregate resource usage from the last hour</CardDescription>
        </CardHeader>
        <CardContent>
          {systemMetrics ? (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-xs text-slate-500">Total Cost</p>
                <p className="text-lg font-bold text-slate-900">${(systemMetrics.total_cost || 0).toFixed(4)}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-xs text-slate-500">Tokens Used</p>
                <p className="text-lg font-bold text-slate-900">{formatNumber(systemMetrics.total_tokens)}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-xs text-slate-500">API Calls</p>
                <p className="text-lg font-bold text-slate-900">{formatNumber(systemMetrics.total_api_calls)}</p>
              </div>
              <div className="p-4 border border-slate-200 rounded-lg">
                <p className="text-xs text-slate-500">Cost per Task</p>
                <p className="text-lg font-bold text-slate-900">${avgCostPerTask.toFixed(4)}</p>
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-600">Cost data has not been reported yet.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
