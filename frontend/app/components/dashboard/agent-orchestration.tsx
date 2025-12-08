
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Network,
  Cpu,
  Activity,
  Play,
  Pause,
  RotateCcw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Zap,
  Brain,
  RefreshCw
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'idle' | 'error' | 'processing' | 'running' | 'completed' | 'failed';
  load: number;
  tasksCompleted: number;
  uptime: string;
  accuracy: number;
  lastActivity: string;
  capabilities?: string[];
}

interface BackendAgent {
  id: string;
  name: string;
  type: string;
  status: string;
  capabilities: string[];
  description: string;
}

export function AgentOrchestration() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const [orchestrationMetrics, setOrchestrationMetrics] = useState({
    totalAgents: 0,
    activeAgents: 0,
    idleAgents: 0,
    errorAgents: 0,
    avgLoad: 58.3,
    totalTasks: 15847,
    tasksPerMinute: 34.5,
    orchestratorHealth: 'optimal'
  });

  useEffect(() => {
    fetchAgents();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAgents, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/agents');
      
      if (!response.ok) {
        throw new Error('Failed to fetch agents');
      }

      const data = await response.json();
      const backendAgents: BackendAgent[] = data?.agents || [];
      
      // Transform backend agents to frontend format with simulated metrics
      const transformedAgents: Agent[] = backendAgents.map((agent, index) => {
        // Generate simulated but consistent metrics based on agent id
        const seed = agent.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const statusOptions: Agent['status'][] = ['idle', 'idle', 'idle', 'active', 'processing'];
        const randomStatus = statusOptions[seed % statusOptions.length];
        
        return {
          id: agent.id,
          name: agent.type,
          type: agent.type,
          status: randomStatus,
          load: 15 + (seed % 70),
          tasksCompleted: 100 + (seed % 3000),
          uptime: `99.${90 + (seed % 9)}%`,
          accuracy: 93 + (seed % 6) + Math.random(),
          lastActivity: randomStatus === 'idle' ? '5 min ago' : randomStatus === 'processing' ? '2 sec ago' : '30 sec ago',
          capabilities: agent.capabilities
        };
      });

      setAgents(transformedAgents);
      
      // Update orchestration metrics with real agent count
      const activeCount = transformedAgents.filter(a => a.status === 'active' || a.status === 'processing').length;
      const idleCount = transformedAgents.filter(a => a.status === 'idle').length;
      const errorCount = transformedAgents.filter(a => a.status === 'error' || a.status === 'failed').length;
      const avgLoad = transformedAgents.reduce((sum, a) => sum + a.load, 0) / transformedAgents.length;

      setOrchestrationMetrics({
        totalAgents: transformedAgents.length,
        activeAgents: activeCount,
        idleAgents: idleCount,
        errorAgents: errorCount,
        avgLoad: Math.round(avgLoad * 10) / 10,
        totalTasks: 15847,
        tasksPerMinute: 34.5,
        orchestratorHealth: 'optimal'
      });

      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700 border-green-200';
      case 'processing': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'idle': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'error': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle2 className="w-4 h-4" />;
      case 'processing': return <Activity className="w-4 h-4 animate-pulse" />;
      case 'idle': return <Clock className="w-4 h-4" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getLoadColor = (load: number) => {
    if (load >= 80) return 'text-red-600';
    if (load >= 60) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6">
      {/* Orchestration Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <Network className="w-8 h-8 text-blue-600" />
              <Badge className="bg-blue-100 text-blue-700 border-0">Total</Badge>
            </div>
            <p className="text-3xl font-bold text-slate-900">{orchestrationMetrics.totalAgents}</p>
            <p className="text-sm text-slate-600 mt-1">Total Agents</p>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <Zap className="w-8 h-8 text-green-600" />
              <Badge className="bg-green-100 text-green-700 border-0">Live</Badge>
            </div>
            <p className="text-3xl font-bold text-slate-900">{orchestrationMetrics.activeAgents}</p>
            <p className="text-sm text-slate-600 mt-1">Active Agents</p>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <Cpu className="w-8 h-8 text-purple-600" />
              <Badge className="bg-purple-100 text-purple-700 border-0">Avg</Badge>
            </div>
            <p className="text-3xl font-bold text-slate-900">{orchestrationMetrics.avgLoad}%</p>
            <p className="text-sm text-slate-600 mt-1">Average Load</p>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <Activity className="w-8 h-8 text-orange-600" />
              <Badge className="bg-orange-100 text-orange-700 border-0">Rate</Badge>
            </div>
            <p className="text-3xl font-bold text-slate-900">{orchestrationMetrics.tasksPerMinute}</p>
            <p className="text-sm text-slate-600 mt-1">Tasks/min</p>
          </CardContent>
        </Card>
      </div>

      {/* Agent Grid */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Network className="w-5 h-5 text-blue-600" />
                Agent Fleet Management
              </CardTitle>
              <CardDescription>Real-time monitoring and control of all agent instances</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 mr-2">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </span>
              <Button size="sm" variant="outline" onClick={fetchAgents} disabled={loading}>
                <RotateCcw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <div 
                key={agent.id} 
                className="p-5 border border-slate-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all duration-200"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Brain className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900">{agent.name}</h4>
                      <p className="text-xs text-slate-500">{agent.id}</p>
                    </div>
                  </div>
                  <Badge className={getStatusColor(agent.status)}>
                    <span className="flex items-center gap-1">
                      {getStatusIcon(agent.status)}
                      {agent.status}
                    </span>
                  </Badge>
                </div>

                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Agent Load</span>
                      <span className={`font-bold ${getLoadColor(agent.load)}`}>{agent.load}%</span>
                    </div>
                    <Progress value={agent.load} className="h-2" />
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
                    <div>
                      <p className="text-xs text-slate-500">Tasks Completed</p>
                      <p className="text-lg font-bold text-slate-900">{agent.tasksCompleted.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Accuracy</p>
                      <p className="text-lg font-bold text-slate-900">{agent.accuracy}%</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Uptime</p>
                      <p className="text-lg font-bold text-slate-900">{agent.uptime}</p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-500">Last Activity</p>
                      <p className="text-lg font-bold text-slate-900">{agent.lastActivity}</p>
                    </div>
                  </div>

                  <div className="flex gap-2 pt-2">
                    <Button size="sm" variant="outline" className="flex-1">
                      <Pause className="w-3 h-3 mr-1" />
                      Pause
                    </Button>
                    <Button size="sm" variant="outline" className="flex-1">
                      <RotateCcw className="w-3 h-3 mr-1" />
                      Restart
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Agent Communication Graph */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5 text-purple-600" />
            Inter-Agent Communication Network
          </CardTitle>
          <CardDescription>
            Agent collaboration matrix showing potential communication pathways ({agents.length} agents registered)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="bg-slate-50 rounded-lg p-8 min-h-[400px] flex items-center justify-center">
              <div className="text-center">
                <RefreshCw className="w-16 h-16 text-slate-400 mx-auto mb-4 animate-spin" />
                <p className="text-slate-600 font-medium">Loading agent network...</p>
              </div>
            </div>
          ) : agents.length === 0 ? (
            <div className="bg-slate-50 rounded-lg p-8 min-h-[400px] flex items-center justify-center">
              <div className="text-center">
                <AlertCircle className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                <p className="text-slate-600 font-medium">No agents available</p>
                <p className="text-sm text-slate-500 mt-2">
                  Please ensure the backend API is running
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Communication Matrix */}
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
                {agents.slice(0, 15).map((agent) => (
                  <div 
                    key={agent.id}
                    className="relative p-4 border-2 rounded-lg bg-gradient-to-br from-white to-slate-50 hover:from-blue-50 hover:to-purple-50 hover:border-blue-300 transition-all duration-300 cursor-pointer group"
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`w-3 h-3 rounded-full ${
                        agent.status === 'active' || agent.status === 'processing' 
                          ? 'bg-green-500 animate-pulse' 
                          : 'bg-slate-300'
                      }`}></div>
                      <Brain className="w-4 h-4 text-blue-600" />
                    </div>
                    <p className="font-semibold text-xs text-slate-900 truncate">{agent.type}</p>
                    <p className="text-[10px] text-slate-500 mt-1">
                      {agent.status} • {agent.load}% load
                    </p>
                    
                    {/* Connection indicator on hover */}
                    <div className="absolute -top-1 -right-1 w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                      <Network className="w-3 h-3 text-white" />
                    </div>
                  </div>
                ))}
              </div>

              {/* Legend */}
              <div className="flex items-center justify-center gap-6 pt-4 border-t border-slate-200">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-xs text-slate-600">Active/Processing</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-slate-300"></div>
                  <span className="text-xs text-slate-600">Idle</span>
                </div>
                <div className="flex items-center gap-2">
                  <Network className="w-4 h-4 text-blue-600" />
                  <span className="text-xs text-slate-600">Communication Ready</span>
                </div>
              </div>

              {agents.length > 15 && (
                <div className="text-center py-2">
                  <p className="text-sm text-slate-500">
                    Showing 15 of {agents.length} agents • Full topology available in production
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
