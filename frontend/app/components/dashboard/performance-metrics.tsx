
'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
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
  Clock,
  CheckCircle2,
  AlertTriangle,
  Activity,
  Zap
} from 'lucide-react';

export function PerformanceMetrics() {
  const [performanceData, setPerformanceData] = useState([
    { time: '00:00', latency: 820, throughput: 145, accuracy: 94.2 },
    { time: '04:00', latency: 750, throughput: 162, accuracy: 94.8 },
    { time: '08:00', latency: 680, throughput: 189, accuracy: 95.1 },
    { time: '12:00', latency: 820, throughput: 178, accuracy: 94.9 },
    { time: '16:00', latency: 730, throughput: 195, accuracy: 95.3 },
    { time: '20:00', latency: 690, throughput: 203, accuracy: 95.7 }
  ]);

  const [taskDistribution, setTaskDistribution] = useState([
    { name: 'Completed', value: 2847, color: '#10b981' },
    { name: 'In Progress', value: 234, color: '#3b82f6' },
    { name: 'Queued', value: 89, color: '#f59e0b' },
    { name: 'Failed', value: 12, color: '#ef4444' }
  ]);

  const [modelMetrics, setModelMetrics] = useState([
    { model: 'ReAct Agent', accuracy: 96.2, latency: 680, throughput: 245 },
    { model: 'Evaluator', accuracy: 94.8, latency: 520, throughput: 312 },
    { model: 'Debate Agent', accuracy: 95.1, latency: 890, throughput: 189 },
    { model: 'Governor', accuracy: 97.3, latency: 450, throughput: 356 }
  ]);

  const [costMetrics, setCostMetrics] = useState([
    { period: 'Jan', compute: 4200, storage: 1200, api: 800 },
    { period: 'Feb', compute: 4800, storage: 1350, api: 920 },
    { period: 'Mar', compute: 5200, storage: 1400, api: 1100 },
    { period: 'Apr', compute: 4900, storage: 1500, api: 980 },
    { period: 'May', compute: 5500, storage: 1600, api: 1250 },
    { period: 'Jun', compute: 6100, storage: 1700, api: 1400 }
  ]);

  return (
    <div className="space-y-6">
      {/* Simulated Data Notice */}
      <Card className="bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
            <p className="text-sm font-medium text-slate-900">
              <strong>Demo Mode:</strong> Performance metrics shown are simulated for demonstration. Connect to production systems to display real performance data.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Real-time Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Activity className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Live</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Average Latency</p>
            <p className="text-4xl font-bold">0.73s</p>
            <p className="text-xs opacity-75 mt-2">↓ 15.2% from baseline</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Zap className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Live</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Throughput</p>
            <p className="text-4xl font-bold">203/hr</p>
            <p className="text-xs opacity-75 mt-2">↑ 24.5% from baseline</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <CheckCircle2 className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Live</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Success Rate</p>
            <p className="text-4xl font-bold">98.4%</p>
            <p className="text-xs opacity-75 mt-2">Target: 95%</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <TrendingUp className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Live</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Model Accuracy</p>
            <p className="text-4xl font-bold">95.7%</p>
            <p className="text-xs opacity-75 mt-2">↑ 3.2% this week</p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle>Latency & Throughput Trends</CardTitle>
            <CardDescription>24-hour performance monitoring</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
                <defs>
                  <linearGradient id="colorLatency" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="time" stroke="#64748b" />
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
                <Area 
                  type="monotone" 
                  dataKey="latency" 
                  stroke="#3b82f6" 
                  fillOpacity={1} 
                  fill="url(#colorLatency)"
                  name="Latency (ms)"
                />
                <Area 
                  type="monotone" 
                  dataKey="throughput" 
                  stroke="#10b981" 
                  fillOpacity={1} 
                  fill="url(#colorThroughput)"
                  name="Throughput (tasks/hr)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle>Task Distribution</CardTitle>
            <CardDescription>Current task status breakdown</CardDescription>
          </CardHeader>
          <CardContent>
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
          </CardContent>
        </Card>
      </div>

      {/* Model-specific Metrics */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle>Agent Model Performance</CardTitle>
          <CardDescription>Comparative analysis of individual agent models</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={modelMetrics}>
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
              <Bar dataKey="accuracy" fill="#10b981" name="Accuracy (%)" />
              <Bar dataKey="latency" fill="#3b82f6" name="Latency (ms)" />
              <Bar dataKey="throughput" fill="#f59e0b" name="Throughput" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Cost Analysis */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle>Resource Cost Analysis</CardTitle>
          <CardDescription>Monthly operational expenses breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={costMetrics}>
              <defs>
                <linearGradient id="colorCompute" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorStorage" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorAPI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="period" stroke="#64748b" />
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
              <Area type="monotone" dataKey="compute" stackId="1" stroke="#3b82f6" fill="url(#colorCompute)" name="Compute ($)" />
              <Area type="monotone" dataKey="storage" stackId="1" stroke="#8b5cf6" fill="url(#colorStorage)" name="Storage ($)" />
              <Area type="monotone" dataKey="api" stackId="1" stroke="#10b981" fill="url(#colorAPI)" name="API Calls ($)" />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
