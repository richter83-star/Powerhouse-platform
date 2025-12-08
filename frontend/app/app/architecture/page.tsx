
'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Network,
  Database,
  Brain,
  Zap,
  Shield,
  GitBranch,
  Cpu,
  Package,
  ArrowRight,
  CheckCircle2,
  Server,
  Cloud,
  Lock,
  Activity
} from 'lucide-react';

interface Agent {
  id: string;
  name: string;
  type: string;
}

type TabValue = 'overview' | 'components' | 'dataflow' | 'infrastructure';

export default function ArchitecturePage() {
  // Use static agent list that matches backend data
  const staticAgents: Agent[] = [
    { id: 'react', name: 'react', type: 'ReActAgent' },
    { id: 'debate', name: 'debate', type: 'DebateAgent' },
    { id: 'evaluator', name: 'evaluator', type: 'EvaluatorAgent' },
    { id: 'governor', name: 'governor', type: 'GovernorAgent' },
    { id: 'planning', name: 'planning', type: 'PlanningAgent' },
    { id: 'memory', name: 'memory', type: 'MemoryAgent' },
    { id: 'reflection', name: 'reflection', type: 'ReflectionAgent' },
    { id: 'tree_of_thought', name: 'tree_of_thought', type: 'TreeOfThoughtAgent' },
    { id: 'chain_of_thought', name: 'chain_of_thought', type: 'ChainOfThoughtAgent' },
    { id: 'multi_agent', name: 'multi_agent', type: 'MultiAgent' },
    { id: 'swarm', name: 'swarm', type: 'SwarmAgent' },
    { id: 'hierarchical', name: 'hierarchical', type: 'HierarchicalAgent' },
    { id: 'curriculum', name: 'curriculum', type: 'CurriculumAgent' },
    { id: 'meta_evolver', name: 'meta_evolver', type: 'MetaEvolverAgent' },
    { id: 'toolformer', name: 'toolformer', type: 'ToolformerAgent' },
    { id: 'voyager', name: 'voyager', type: 'VoyagerAgent' },
    { id: 'generative', name: 'generative', type: 'GenerativeAgent' },
    { id: 'adaptive_memory', name: 'adaptive_memory', type: 'AdaptiveMemoryAgent' },
    { id: 'auto_loop', name: 'auto_loop', type: 'AutoLoopAgent' }
  ];

  const [agents, setAgents] = useState<Agent[]>(staticAgents);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<TabValue>('overview');
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50">
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 bg-clip-text text-transparent mb-2">
            System Architecture
          </h1>
          <p className="text-slate-600 text-lg">
            Comprehensive view of the multi-agent platform infrastructure and component interactions
          </p>
        </div>

        <div className="space-y-6">
          <div className="bg-white/60 backdrop-blur-sm border border-slate-200 p-1 rounded-lg inline-flex gap-1">
            <Button
              variant={activeTab === 'overview' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('overview')}
              className="px-4 py-2"
            >
              System Overview
            </Button>
            <Button
              variant={activeTab === 'components' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('components')}
              className="px-4 py-2"
            >
              Core Components
            </Button>
            <Button
              variant={activeTab === 'dataflow' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('dataflow')}
              className="px-4 py-2"
            >
              Data Flow
            </Button>
            <Button
              variant={activeTab === 'infrastructure' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('infrastructure')}
              className="px-4 py-2"
            >
              Infrastructure
            </Button>
          </div>

          {activeTab === 'overview' && (<div className="space-y-6">
            {/* Architecture Diagram */}
            <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Network className="w-5 h-5 text-blue-600" />
                  Multi-Agent System Architecture
                </CardTitle>
                <CardDescription>High-level system design and component relationships</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg p-8">
                  <div className="space-y-8">
                    {/* Layer 1: API Gateway */}
                    <div className="flex justify-center">
                      <div className="bg-blue-600 px-6 py-4 rounded-lg text-white font-semibold text-center min-w-[300px]">
                        <Cloud className="w-6 h-6 mx-auto mb-2" />
                        API Gateway & Load Balancer
                      </div>
                    </div>

                    <div className="flex justify-center">
                      <ArrowRight className="w-6 h-6 text-slate-400 rotate-90" />
                    </div>

                    {/* Layer 2: Core Services */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="bg-purple-600 p-4 rounded-lg text-white text-center">
                        <Brain className="w-6 h-6 mx-auto mb-2" />
                        <p className="font-semibold text-sm">Agent Orchestrator</p>
                      </div>
                      <div className="bg-green-600 p-4 rounded-lg text-white text-center">
                        <Activity className="w-6 h-6 mx-auto mb-2" />
                        <p className="font-semibold text-sm">Performance Monitor</p>
                      </div>
                      <div className="bg-orange-600 p-4 rounded-lg text-white text-center">
                        <Zap className="w-6 h-6 mx-auto mb-2" />
                        <p className="font-semibold text-sm">Learning System</p>
                      </div>
                      <div className="bg-red-600 p-4 rounded-lg text-white text-center">
                        <Shield className="w-6 h-6 mx-auto mb-2" />
                        <p className="font-semibold text-sm">Plugin Manager</p>
                      </div>
                    </div>

                    <div className="flex justify-center">
                      <ArrowRight className="w-6 h-6 text-slate-400 rotate-90" />
                    </div>

                    {/* Layer 3: Agent Pool */}
                    <div className="bg-slate-700 p-6 rounded-lg">
                      <p className="text-white font-semibold text-center mb-4">
                        Agent Pool ({loading ? '...' : agents.length} Active {agents.length === 1 ? 'Instance' : 'Instances'})
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                        {loading ? (
                          Array(6).fill(0).map((_, i) => (
                            <div key={i} className="bg-slate-600 p-3 rounded text-white text-center text-xs animate-pulse">
                              <Cpu className="w-4 h-4 mx-auto mb-1" />
                              Loading...
                            </div>
                          ))
                        ) : (
                          agents.slice(0, 12).map((agent) => (
                            <div key={agent.id} className="bg-slate-600 p-3 rounded text-white text-center text-xs hover:bg-slate-500 transition-colors" title={agent.type}>
                              <Cpu className="w-4 h-4 mx-auto mb-1" />
                              {agent.name}
                            </div>
                          ))
                        )}
                      </div>
                      {!loading && agents.length > 12 && (
                        <p className="text-slate-300 text-xs text-center mt-3">
                          + {agents.length - 12} more agents available
                        </p>
                      )}
                    </div>

                    <div className="flex justify-center">
                      <ArrowRight className="w-6 h-6 text-slate-400 rotate-90" />
                    </div>

                    {/* Layer 4: Data Layer */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="bg-cyan-600 p-4 rounded-lg text-white text-center">
                        <Database className="w-6 h-6 mx-auto mb-2" />
                        <p className="font-semibold text-sm">PostgreSQL</p>
                        <p className="text-xs opacity-75">Primary Database</p>
                      </div>
                      <div className="bg-teal-600 p-4 rounded-lg text-white text-center">
                        <Server className="w-6 h-6 mx-auto mb-2" />
                        <p className="font-semibold text-sm">Redis Cache</p>
                        <p className="text-xs opacity-75">Memory Store</p>
                      </div>
                      <div className="bg-indigo-600 p-4 rounded-lg text-white text-center">
                        <Package className="w-6 h-6 mx-auto mb-2" />
                        <p className="font-semibold text-sm">Vector DB</p>
                        <p className="text-xs opacity-75">Embeddings</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Key Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-3 bg-blue-100 rounded-lg">
                      <Shield className="w-6 h-6 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900">Security & Isolation</h3>
                  </div>
                  <ul className="space-y-2 text-sm text-slate-600">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Sandboxed plugin execution environment</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Cryptographic signature verification</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Role-based access control (RBAC)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>End-to-end encryption for data transfer</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-3 bg-purple-100 rounded-lg">
                      <Zap className="w-6 h-6 text-purple-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900">Scalability</h3>
                  </div>
                  <ul className="space-y-2 text-sm text-slate-600">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Horizontal agent scaling (auto-scale)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Distributed task queue processing</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Multi-region deployment support</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Load balancing across agent pools</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>

              <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-3 bg-green-100 rounded-lg">
                      <Activity className="w-6 h-6 text-green-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-900">Observability</h3>
                  </div>
                  <ul className="space-y-2 text-sm text-slate-600">
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Real-time performance monitoring</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Distributed tracing and logging</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Automated alerting and diagnostics</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                      <span>Custom metrics and dashboards</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>)}

          {activeTab === 'components' && (<div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {[
                {
                  title: 'Agent Orchestrator',
                  icon: Brain,
                  color: 'purple',
                  description: 'Coordinates and manages all agent activities',
                  features: [
                    'Dynamic task distribution',
                    'Agent lifecycle management',
                    'Inter-agent communication',
                    'State synchronization'
                  ]
                },
                {
                  title: 'Performance Monitor',
                  icon: Activity,
                  color: 'green',
                  description: 'Real-time system health and performance tracking',
                  features: [
                    'Metric collection and aggregation',
                    'Anomaly detection',
                    'Auto-scaling triggers',
                    'Performance reporting'
                  ]
                },
                {
                  title: 'Learning System',
                  icon: Zap,
                  color: 'orange',
                  description: 'Continuous model improvement and retraining',
                  features: [
                    'Autonomous retraining triggers',
                    'Model versioning',
                    'A/B testing framework',
                    'Performance benchmarking'
                  ]
                },
                {
                  title: 'Plugin Manager',
                  icon: Package,
                  color: 'red',
                  description: 'Secure plugin loading and execution',
                  features: [
                    'Signature verification',
                    'Sandboxed execution',
                    'Dependency management',
                    'Version control'
                  ]
                },
                {
                  title: 'CI/CD Pipeline',
                  icon: GitBranch,
                  color: 'blue',
                  description: 'Automated deployment and update management',
                  features: [
                    'Version detection',
                    'Simulation testing',
                    'Gradual rollout',
                    'Rollback capability'
                  ]
                },
                {
                  title: 'Goal-Driven System',
                  icon: CheckCircle2,
                  color: 'cyan',
                  description: 'Autonomous goal setting and execution',
                  features: [
                    'Predictive forecasting',
                    'Goal prioritization',
                    'Progress tracking',
                    'Self-optimization'
                  ]
                }
              ].map((component, index) => (
                <Card key={index} className="bg-white/80 backdrop-blur-sm border-slate-200">
                  <CardHeader>
                    <div className="flex items-center gap-3">
                      <div className={`p-3 bg-${component.color}-100 rounded-lg`}>
                        <component.icon className={`w-6 h-6 text-${component.color}-600`} />
                      </div>
                      <div>
                        <CardTitle>{component.title}</CardTitle>
                        <CardDescription>{component.description}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {component.features.map((feature, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-slate-600">
                          <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>)}

          {activeTab === 'dataflow' && (<div className="space-y-6">
            <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
              <CardHeader>
                <CardTitle>Data Flow Architecture</CardTitle>
                <CardDescription>How data moves through the system</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-slate-50 rounded-lg p-8 min-h-[600px]">
                  <div className="text-center">
                    <Network className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                    <p className="text-slate-600 font-medium">Interactive Data Flow Diagram</p>
                    <p className="text-sm text-slate-500 mt-2">
                      Detailed visualization of data pipelines and transformations
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>)}

          {activeTab === 'infrastructure' && (<div className="space-y-6">
            <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
              <CardHeader>
                <CardTitle>Infrastructure & Deployment</CardTitle>
                <CardDescription>Cloud infrastructure and deployment topology</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-6 border-2 border-blue-200 rounded-lg bg-blue-50">
                      <Cloud className="w-8 h-8 text-blue-600 mb-3" />
                      <h3 className="font-semibold text-slate-900 mb-2">Cloud Provider</h3>
                      <p className="text-sm text-slate-600">AWS Multi-Region Deployment</p>
                      <Badge className="mt-2">Active</Badge>
                    </div>
                    <div className="p-6 border-2 border-purple-200 rounded-lg bg-purple-50">
                      <Server className="w-8 h-8 text-purple-600 mb-3" />
                      <h3 className="font-semibold text-slate-900 mb-2">Compute Resources</h3>
                      <p className="text-sm text-slate-600">Kubernetes Cluster (24 nodes)</p>
                      <Badge className="mt-2">Scaled</Badge>
                    </div>
                    <div className="p-6 border-2 border-green-200 rounded-lg bg-green-50">
                      <Lock className="w-8 h-8 text-green-600 mb-3" />
                      <h3 className="font-semibold text-slate-900 mb-2">Security</h3>
                      <p className="text-sm text-slate-600">VPC, WAF, SSL/TLS Encryption</p>
                      <Badge className="mt-2">Secured</Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>)}
        </div>
      </div>
    </div>
  );
}
