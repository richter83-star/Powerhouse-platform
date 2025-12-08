
'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AgentCard } from '@/components/agent-card';
import { Agent } from '@/lib/types';
import { Users, Activity, CheckCircle, XCircle, RefreshCw, Sparkles, Brain, Database, Network, BarChart3, Cpu } from 'lucide-react';

export default function AgentsPage() {
  const { data: session, status } = useSession() || {};
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router]);

  useEffect(() => {
    if (status === 'authenticated') {
      fetchAgents();
    }
  }, [status]);

  const fetchAgents = async () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    try {
      console.log('[Agents] Fetching from:', `${apiUrl}/api/v1/agents`);
      
      const response = await fetch(`${apiUrl}/api/v1/agents`, {
        cache: 'no-store',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`Backend returned error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('[Agents] Successfully fetched:', data?.agents?.length || 0, 'agents');
      
      if (!data?.agents || data.agents.length === 0) {
        console.warn('[Agents] Backend returned zero agents!');
        setError('Backend is running but returned zero agents. Check backend logs.');
      } else {
        setError('');
      }
      
      setAgents(data?.agents || []);
    } catch (err: any) {
      console.error('[Agents] Fetch error:', err);
      
      // Provide specific error messages
      if (err?.message?.includes('Failed to fetch') || err?.name === 'TypeError') {
        setError('❌ Cannot connect to backend! Make sure backend is running on port 8001. Run DIAGNOSE.bat to check.');
      } else if (err?.message?.includes('NetworkError')) {
        setError('❌ Network error: Backend is not reachable. Ensure backend is running (run START.bat).');
      } else {
        setError(err?.message || '❌ Failed to fetch agents. Check console for details.');
      }
      
      console.error('[Agents] Full error details:', err);
      console.error('[Agents] Backend URL:', `${apiUrl}/api/v1/agents`);
      console.error('[Agents] Possible causes:');
      console.error('  1. Backend is not running → Run START.bat');
      console.error('  2. Backend crashed → Check backend terminal for errors');
      console.error('  3. Wrong port → Backend should be on port 8001');
    } finally {
      setLoading(false);
    }
  };

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-300">Loading agents...</p>
        </div>
      </div>
    );
  }

  if (status === 'unauthenticated') {
    return null;
  }

  const activeAgents = agents?.filter(a => a?.status === 'idle')?.length || 0;
  const busyAgents = agents?.filter(a => a?.status === 'running')?.length || 0;
  const inactiveAgents = agents?.filter(a => a?.status === 'failed')?.length || 0;

  const agentCategories = [
    { name: 'Reasoning', count: 4, icon: Brain, color: 'from-blue-500 to-cyan-500' },
    { name: 'Memory', count: 4, icon: Database, color: 'from-green-500 to-emerald-500' },
    { name: 'Coordination', count: 4, icon: Network, color: 'from-purple-500 to-pink-500' },
    { name: 'Analysis', count: 4, icon: BarChart3, color: 'from-orange-500 to-amber-500' },
    { name: 'Autonomous', count: 3, icon: Cpu, color: 'from-pink-500 to-rose-500' },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-pink-600/10 animate-gradient-xy" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className={`mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl">
                <Users className="w-7 h-7 text-white" />
              </div>
              <div>
                <Badge className="mb-2 bg-purple-500/20 text-purple-300 border-purple-500/30 backdrop-blur-xl">
                  <Sparkles className="w-3 h-3 mr-1" />
                  19 Specialized Agents
                </Badge>
                <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-purple-400 bg-clip-text text-transparent">
                  Agent Fleet Management
                </h1>
                <p className="text-slate-300 mt-1">
                  Monitor and manage your multi-agent intelligence network
                </p>
              </div>
            </div>
            <Button
              onClick={() => {
                setLoading(true);
                fetchAgents();
              }}
              disabled={loading}
              className="flex items-center gap-2 bg-white/5 backdrop-blur-xl border border-white/10 hover:bg-white/10 transition-all duration-300 hover:scale-105"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className={`grid grid-cols-1 md:grid-cols-4 gap-6 mb-8 transition-all duration-700 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Total Agents</p>
                  <p className="text-3xl font-bold text-white">{agents?.length || 0}</p>
                </div>
                <Activity className="w-8 h-8 text-blue-400 group-hover:scale-110 transition-transform duration-300" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Active</p>
                  <p className="text-3xl font-bold text-green-400">{activeAgents}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-400 group-hover:scale-110 transition-transform duration-300" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Busy</p>
                  <p className="text-3xl font-bold text-yellow-400">{busyAgents}</p>
                </div>
                <Activity className="w-8 h-8 text-yellow-400 group-hover:scale-110 transition-transform duration-300" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400 mb-1">Inactive</p>
                  <p className="text-3xl font-bold text-slate-400">{inactiveAgents}</p>
                </div>
                <XCircle className="w-8 h-8 text-slate-400 group-hover:scale-110 transition-transform duration-300" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Agent Categories */}
        <div className={`mb-12 transition-all duration-700 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Agent Categories
            </h2>
            <p className="text-slate-400">Specialized agents organized by capability and function</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {agentCategories.map((category, index) => {
              const Icon = category.icon;
              return (
                <Card
                  key={index}
                  className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group cursor-pointer"
                >
                  <CardContent className="p-6 text-center">
                    <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${category.color} p-0.5 group-hover:scale-110 transition-transform duration-300`}>
                      <div className="w-full h-full bg-slate-950 rounded-2xl flex items-center justify-center">
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                    </div>
                    <p className="font-semibold text-lg mb-1 text-white">{category.name}</p>
                    <p className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                      {category.count}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <Card className="mb-8 bg-red-500/10 backdrop-blur-xl border-red-500/30">
            <CardContent className="pt-6">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-semibold text-red-300">Connection Error</h4>
                    <p className="text-sm text-red-200 mb-2">{error}</p>
                    <p className="text-xs text-red-300">
                      Make sure the backend is running on port 8001. Check the console for details.
                    </p>
                  </div>
                </div>
                <Button
                  onClick={() => {
                    setLoading(true);
                    setError('');
                    fetchAgents();
                  }}
                  variant="outline"
                  size="sm"
                  className="flex items-center gap-2 border-red-500/30 hover:bg-red-500/20"
                >
                  <RefreshCw className="w-3 h-3" />
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Agents Grid */}
        <div className={`transition-all duration-700 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
            Available Agents
          </h2>
          {agents && agents.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {agents.map((agent) => (
                <AgentCard key={agent?.id || Math.random()} agent={agent} />
              ))}
            </div>
          ) : (
            <Card className="p-12 text-center bg-white/5 backdrop-blur-xl border-white/10">
              <Users className="w-16 h-16 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">
                No Agents Available
              </h3>
              <p className="text-slate-400">
                Please check your backend connection or contact support.
              </p>
            </Card>
          )}
        </div>

        {/* Agent Categories Details */}
        <Card className={`mt-12 bg-white/5 backdrop-blur-xl border-white/10 transition-all duration-700 delay-400 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <CardHeader>
            <CardTitle className="text-2xl bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Agent Categories & Capabilities
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {/* Core Analysis Agents */}
              <div>
                <h3 className="text-lg font-bold text-blue-300 mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                  Core Analysis Agents (4)
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { name: 'ReAct', capabilities: ['Structured reasoning', 'Action planning', 'Analytical processing'] },
                    { name: 'Evaluator', capabilities: ['Quality assessment', 'Risk scoring', 'Confidence measurement'] },
                    { name: 'Debate', capabilities: ['Multi-perspective analysis', 'Argument synthesis', 'Stakeholder modeling'] },
                    { name: 'Governor', capabilities: ['Policy enforcement', 'Preflight validation', 'Safety checks'] },
                  ].map((agent) => (
                    <div key={agent.name} className="p-4 bg-blue-500/10 backdrop-blur-xl rounded-xl border border-blue-500/20 hover:border-blue-500/40 transition-all duration-300 hover:scale-105">
                      <h4 className="font-semibold text-white mb-2">{agent.name}</h4>
                      <ul className="space-y-1 text-xs text-slate-300">
                        {agent.capabilities.map((cap, idx) => (
                          <li key={idx}>• {cap}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* Advanced Reasoning Agents */}
              <div>
                <h3 className="text-lg font-bold text-purple-300 mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-purple-400"></div>
                  Advanced Reasoning Agents (4)
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { name: 'Chain of Thought', capabilities: ['Sequential reasoning', 'Step-by-step analysis', 'Transparent thinking'] },
                    { name: 'Tree of Thought', capabilities: ['Branching reasoning', 'Path exploration', 'Decision tree analysis'] },
                    { name: 'Planning', capabilities: ['Strategic planning', 'Task decomposition', 'Workflow optimization'] },
                    { name: 'Reflection', capabilities: ['Self-assessment', 'Iterative improvement', 'Error correction'] },
                  ].map((agent) => (
                    <div key={agent.name} className="p-4 bg-purple-500/10 backdrop-blur-xl rounded-xl border border-purple-500/20 hover:border-purple-500/40 transition-all duration-300 hover:scale-105">
                      <h4 className="font-semibold text-white mb-2">{agent.name}</h4>
                      <ul className="space-y-1 text-xs text-slate-300">
                        {agent.capabilities.map((cap, idx) => (
                          <li key={idx}>• {cap}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* Memory & Learning Agents */}
              <div>
                <h3 className="text-lg font-bold text-green-300 mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-400"></div>
                  Memory & Learning Agents (4)
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { name: 'Memory', capabilities: ['Context storage', 'Information retrieval', 'Knowledge management'] },
                    { name: 'Adaptive Memory', capabilities: ['Dynamic memory', 'Context adaptation', 'Priority management'] },
                    { name: 'Curriculum', capabilities: ['Progressive learning', 'Difficulty adaptation', 'Skill building'] },
                    { name: 'Meta Evolver', capabilities: ['Strategy evolution', 'Meta-learning', 'Adaptive optimization'] },
                  ].map((agent) => (
                    <div key={agent.name} className="p-4 bg-green-500/10 backdrop-blur-xl rounded-xl border border-green-500/20 hover:border-green-500/40 transition-all duration-300 hover:scale-105">
                      <h4 className="font-semibold text-white mb-2">{agent.name}</h4>
                      <ul className="space-y-1 text-xs text-slate-300">
                        {agent.capabilities.map((cap, idx) => (
                          <li key={idx}>• {cap}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* Coordination & Execution Agents */}
              <div>
                <h3 className="text-lg font-bold text-orange-300 mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-orange-400"></div>
                  Coordination & Execution Agents (4)
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {[
                    { name: 'Multi-Agent', capabilities: ['Parallel execution', 'Agent coordination', 'Result aggregation'] },
                    { name: 'Swarm', capabilities: ['Collective intelligence', 'Distributed processing', 'Consensus building'] },
                    { name: 'Hierarchical', capabilities: ['Hierarchical planning', 'Task delegation', 'Supervision'] },
                    { name: 'Toolformer', capabilities: ['Tool selection', 'API integration', 'Function calling'] },
                  ].map((agent) => (
                    <div key={agent.name} className="p-4 bg-orange-500/10 backdrop-blur-xl rounded-xl border border-orange-500/20 hover:border-orange-500/40 transition-all duration-300 hover:scale-105">
                      <h4 className="font-semibold text-white mb-2">{agent.name}</h4>
                      <ul className="space-y-1 text-xs text-slate-300">
                        {agent.capabilities.map((cap, idx) => (
                          <li key={idx}>• {cap}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>

              {/* Specialized & Autonomous Agents */}
              <div>
                <h3 className="text-lg font-bold text-yellow-300 mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
                  Specialized & Autonomous Agents (3)
                </h3>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { name: 'Generative', capabilities: ['Content generation', 'Scenario creation', 'Synthetic data'] },
                    { name: 'Voyager', capabilities: ['Exploration', 'Discovery', 'Novel solution generation'] },
                    { name: 'Auto Loop', capabilities: ['Autonomous operation', 'Self-direction', 'Continuous improvement'] },
                  ].map((agent) => (
                    <div key={agent.name} className="p-4 bg-yellow-500/10 backdrop-blur-xl rounded-xl border border-yellow-500/20 hover:border-yellow-500/40 transition-all duration-300 hover:scale-105">
                      <h4 className="font-semibold text-white mb-2">{agent.name}</h4>
                      <ul className="space-y-1 text-xs text-slate-300">
                        {agent.capabilities.map((cap, idx) => (
                          <li key={idx}>• {cap}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
