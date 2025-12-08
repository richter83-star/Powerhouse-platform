
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  GitBranch,
  CheckCircle2,
  Clock,
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  ArrowRight,
  Package,
  TestTube,
  Rocket,
  Shield
} from 'lucide-react';

interface Deployment {
  id: string;
  version: string;
  status: 'success' | 'in-progress' | 'failed' | 'pending';
  environment: string;
  timestamp: string;
  duration: string;
  testsPassed: number;
  testsTotal: number;
  rolloutProgress: number;
}

export default function CICDPage() {
  const [deployments, setDeployments] = useState<Deployment[]>([
    {
      id: 'deploy-001',
      version: 'v2.47.3',
      status: 'success',
      environment: 'Production',
      timestamp: '2024-06-15 14:30:00',
      duration: '4m 23s',
      testsPassed: 847,
      testsTotal: 847,
      rolloutProgress: 100
    },
    {
      id: 'deploy-002',
      version: 'v2.47.2',
      status: 'in-progress',
      environment: 'Staging',
      timestamp: '2024-06-15 14:25:00',
      duration: '2m 15s',
      testsPassed: 723,
      testsTotal: 847,
      rolloutProgress: 65
    },
    {
      id: 'deploy-003',
      version: 'v2.47.1',
      status: 'success',
      environment: 'Production',
      timestamp: '2024-06-14 09:15:00',
      duration: '4m 18s',
      testsPassed: 845,
      testsTotal: 845,
      rolloutProgress: 100
    }
  ]);

  const [pipelineStages, setPipelineStages] = useState([
    { name: 'Version Detection', status: 'completed', duration: '15s' },
    { name: 'Security Scan', status: 'completed', duration: '45s' },
    { name: 'Unit Tests', status: 'completed', duration: '1m 20s' },
    { name: 'Integration Tests', status: 'completed', duration: '2m 10s' },
    { name: 'Simulation Testing', status: 'in-progress', duration: '1m 45s' },
    { name: 'Gradual Rollout', status: 'pending', duration: '-' },
    { name: 'Health Check', status: 'pending', duration: '-' }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': case 'completed': return 'bg-green-100 text-green-700 border-green-200';
      case 'in-progress': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'failed': return 'bg-red-100 text-red-700 border-red-200';
      case 'pending': return 'bg-slate-100 text-slate-700 border-slate-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': case 'completed': return <CheckCircle2 className="w-4 h-4" />;
      case 'in-progress': return <Clock className="w-4 h-4 animate-spin" />;
      case 'failed': return <AlertCircle className="w-4 h-4" />;
      case 'pending': return <Clock className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-50">
      <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 via-blue-900 to-slate-900 bg-clip-text text-transparent mb-2">
                CI/CD Pipeline
              </h1>
              <p className="text-slate-600 text-lg">
                Autonomous deployment system with simulation testing and controlled rollouts
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline">
                <RotateCcw className="w-4 h-4 mr-2" />
                Rollback
              </Button>
              <Button>
                <Rocket className="w-4 h-4 mr-2" />
                New Deployment
              </Button>
            </div>
          </div>
        </div>

        {/* Pipeline Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <GitBranch className="w-8 h-8 text-blue-600" />
                <Badge className="bg-blue-100 text-blue-700 border-0">Total</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">47</p>
              <p className="text-sm text-slate-600 mt-1">Deployments</p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
                <Badge className="bg-green-100 text-green-700 border-0">Success</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">98.7%</p>
              <p className="text-sm text-slate-600 mt-1">Success Rate</p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <Clock className="w-8 h-8 text-purple-600" />
                <Badge className="bg-purple-100 text-purple-700 border-0">Avg</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">4.2m</p>
              <p className="text-sm text-slate-600 mt-1">Deploy Time</p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <TestTube className="w-8 h-8 text-orange-600" />
                <Badge className="bg-orange-100 text-orange-700 border-0">Tests</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">847</p>
              <p className="text-sm text-slate-600 mt-1">Test Cases</p>
            </CardContent>
          </Card>
        </div>

        {/* Current Pipeline Status */}
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200 mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-blue-600" />
              Current Pipeline Execution
            </CardTitle>
            <CardDescription>
              Version v2.47.3 • Initiated by System Auto-Update
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pipelineStages.map((stage, index) => (
                <div key={index} className="flex items-center gap-4">
                  <div className="flex items-center gap-3 min-w-[250px]">
                    <Badge className={getStatusColor(stage.status)}>
                      <span className="flex items-center gap-1">
                        {getStatusIcon(stage.status)}
                        {stage.status}
                      </span>
                    </Badge>
                    <span className="font-medium text-slate-900">{stage.name}</span>
                  </div>
                  <div className="flex-1">
                    <Progress 
                      value={
                        stage.status === 'completed' ? 100 : 
                        stage.status === 'in-progress' ? 65 : 
                        0
                      } 
                      className="h-2" 
                    />
                  </div>
                  <span className="text-sm text-slate-500 min-w-[60px]">{stage.duration}</span>
                  {index < pipelineStages.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Deployment Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <TestTube className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900">Simulation Testing</h3>
              </div>
              <p className="text-sm text-slate-600 mb-4">
                Run updates through comprehensive simulation environment before production
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Isolated test environment</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Automated regression testing</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Performance benchmarking</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Rocket className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900">Gradual Rollout</h3>
              </div>
              <p className="text-sm text-slate-600 mb-4">
                Controlled deployment with automatic rollback on performance degradation
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Canary deployment strategy</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Real-time health monitoring</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Automatic rollback triggers</span>
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <Shield className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900">Version Control</h3>
              </div>
              <p className="text-sm text-slate-600 mb-4">
                Comprehensive version tracking with one-click rollback capabilities
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Semantic versioning</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Change log generation</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600 mt-0.5" />
                  <span>Dependency tracking</span>
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* Deployment History */}
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle>Deployment History</CardTitle>
            <CardDescription>Recent deployments across all environments</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {deployments.map((deployment) => (
                <div 
                  key={deployment.id} 
                  className="p-6 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        <Package className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="text-lg font-semibold text-slate-900">{deployment.version}</h3>
                          <Badge variant="outline">{deployment.environment}</Badge>
                        </div>
                        <p className="text-sm text-slate-500">{deployment.timestamp}</p>
                      </div>
                    </div>
                    <Badge className={getStatusColor(deployment.status)}>
                      <span className="flex items-center gap-1">
                        {getStatusIcon(deployment.status)}
                        {deployment.status}
                      </span>
                    </Badge>
                  </div>

                  <div className="grid grid-cols-3 gap-6 mb-4">
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Duration</p>
                      <p className="text-lg font-semibold text-slate-900">{deployment.duration}</p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Tests Passed</p>
                      <p className="text-lg font-semibold text-slate-900">
                        {deployment.testsPassed} / {deployment.testsTotal}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-slate-600 mb-1">Rollout Progress</p>
                      <p className="text-lg font-semibold text-slate-900">{deployment.rolloutProgress}%</p>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-slate-600">Deployment Progress</span>
                      <span className="font-semibold text-slate-900">{deployment.rolloutProgress}%</span>
                    </div>
                    <Progress value={deployment.rolloutProgress} className="h-2" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
