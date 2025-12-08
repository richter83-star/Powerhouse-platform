
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Package,
  CheckCircle2,
  AlertCircle,
  Clock,
  Download,
  Upload,
  Settings,
  Shield,
  Play,
  Pause,
  Trash2
} from 'lucide-react';

interface Plugin {
  id: string;
  name: string;
  version: string;
  status: 'active' | 'inactive' | 'pending' | 'error';
  author: string;
  description: string;
  installDate: string;
  lastUpdate: string;
  dependencies: string[];
  verified: boolean;
}

export default function PluginsPage() {
  const [plugins, setPlugins] = useState<Plugin[]>([
    {
      id: 'plugin-001',
      name: 'Advanced Analytics',
      version: 'v1.2.3',
      status: 'active',
      author: 'Powerhouse Team',
      description: 'Enhanced analytics and reporting capabilities for compliance data',
      installDate: '2024-01-15',
      lastUpdate: '2024-06-12',
      dependencies: ['pandas', 'numpy', 'matplotlib'],
      verified: true
    },
    {
      id: 'plugin-002',
      name: 'Custom Validators',
      version: 'v2.0.1',
      status: 'active',
      author: 'Security Division',
      description: 'Industry-specific validation rules and compliance checks',
      installDate: '2024-02-20',
      lastUpdate: '2024-06-08',
      dependencies: ['pydantic', 'jsonschema'],
      verified: true
    },
    {
      id: 'plugin-003',
      name: 'External API Connector',
      version: 'v0.9.5',
      status: 'inactive',
      author: 'Integration Team',
      description: 'Connect to external compliance databases and regulatory APIs',
      installDate: '2024-03-10',
      lastUpdate: '2024-05-22',
      dependencies: ['requests', 'aiohttp'],
      verified: true
    },
    {
      id: 'plugin-004',
      name: 'ML Model Extensions',
      version: 'v1.5.0',
      status: 'active',
      author: 'AI Research',
      description: 'Additional machine learning models for specialized tasks',
      installDate: '2024-04-05',
      lastUpdate: '2024-06-15',
      dependencies: ['tensorflow', 'torch', 'scikit-learn'],
      verified: true
    }
  ]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700 border-green-200';
      case 'inactive': return 'bg-slate-100 text-slate-700 border-slate-200';
      case 'pending': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'error': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle2 className="w-4 h-4" />;
      case 'inactive': return <Clock className="w-4 h-4" />;
      case 'pending': return <Clock className="w-4 h-4" />;
      case 'error': return <AlertCircle className="w-4 h-4" />;
      default: return <Package className="w-4 h-4" />;
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
                Plugin Management
              </h1>
              <p className="text-slate-600 text-lg">
                Secure plugin architecture with cryptographic verification and sandboxed execution
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline">
                <Download className="w-4 h-4 mr-2" />
                Browse Repository
              </Button>
              <Button>
                <Upload className="w-4 h-4 mr-2" />
                Upload Plugin
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <Package className="w-8 h-8 text-blue-600" />
                <Badge className="bg-blue-100 text-blue-700 border-0">Total</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">{plugins.length}</p>
              <p className="text-sm text-slate-600 mt-1">Installed Plugins</p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
                <Badge className="bg-green-100 text-green-700 border-0">Active</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">
                {plugins.filter(p => p.status === 'active').length}
              </p>
              <p className="text-sm text-slate-600 mt-1">Active Plugins</p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <Shield className="w-8 h-8 text-purple-600" />
                <Badge className="bg-purple-100 text-purple-700 border-0">Verified</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">
                {plugins.filter(p => p.verified).length}
              </p>
              <p className="text-sm text-slate-600 mt-1">Verified Plugins</p>
            </CardContent>
          </Card>

          <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <AlertCircle className="w-8 h-8 text-yellow-600" />
                <Badge className="bg-yellow-100 text-yellow-700 border-0">Updates</Badge>
              </div>
              <p className="text-3xl font-bold text-slate-900">3</p>
              <p className="text-sm text-slate-600 mt-1">Updates Available</p>
            </CardContent>
          </Card>
        </div>

        {/* Security Features */}
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200 mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-600" />
              Security & Verification
            </CardTitle>
            <CardDescription>
              All plugins undergo cryptographic verification and run in sandboxed environments
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Shield className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2">Signature Verification</h4>
                  <p className="text-sm text-slate-600">
                    All plugins are cryptographically signed and verified before execution
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Package className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2">Sandboxed Execution</h4>
                  <p className="text-sm text-slate-600">
                    Isolated runtime environment with restricted system access
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-green-100 rounded-lg">
                  <CheckCircle2 className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2">Dependency Scanning</h4>
                  <p className="text-sm text-slate-600">
                    Automated vulnerability scanning for all plugin dependencies
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Plugin List */}
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle>Installed Plugins</CardTitle>
            <CardDescription>Manage and configure your plugin ecosystem</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {plugins.map((plugin) => (
                <div 
                  key={plugin.id} 
                  className="p-6 border border-slate-200 rounded-lg hover:border-blue-300 hover:shadow-md transition-all"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        <Package className="w-6 h-6 text-blue-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-semibold text-slate-900">{plugin.name}</h3>
                          <Badge variant="outline">{plugin.version}</Badge>
                          {plugin.verified && (
                            <Badge className="bg-green-100 text-green-700 border-0">
                              <Shield className="w-3 h-3 mr-1" />
                              Verified
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-600 mb-3">{plugin.description}</p>
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span>Author: {plugin.author}</span>
                          <span>•</span>
                          <span>Installed: {plugin.installDate}</span>
                          <span>•</span>
                          <span>Last Update: {plugin.lastUpdate}</span>
                        </div>
                      </div>
                    </div>
                    <Badge className={getStatusColor(plugin.status)}>
                      <span className="flex items-center gap-1">
                        {getStatusIcon(plugin.status)}
                        {plugin.status}
                      </span>
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-600">Dependencies:</span>
                      <div className="flex gap-2">
                        {plugin.dependencies.map((dep, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {dep}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline">
                        <Settings className="w-3 h-3 mr-1" />
                        Configure
                      </Button>
                      {plugin.status === 'active' ? (
                        <Button size="sm" variant="outline">
                          <Pause className="w-3 h-3 mr-1" />
                          Deactivate
                        </Button>
                      ) : (
                        <Button size="sm" variant="outline">
                          <Play className="w-3 h-3 mr-1" />
                          Activate
                        </Button>
                      )}
                      <Button size="sm" variant="outline" className="text-red-600 hover:text-red-700">
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
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
