
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import {
  Brain,
  TrendingUp,
  Target,
  Zap,
  BookOpen,
  Award,
  ArrowUpRight,
  RefreshCw
} from 'lucide-react';

export function LearningAnalytics() {
  const [accuracyTrend, setAccuracyTrend] = useState([
    { epoch: 1, train: 78.2, validation: 76.5, test: 75.8 },
    { epoch: 5, train: 85.4, validation: 83.7, test: 82.9 },
    { epoch: 10, train: 90.1, validation: 88.4, test: 87.6 },
    { epoch: 15, train: 93.2, validation: 91.5, test: 90.8 },
    { epoch: 20, train: 95.3, validation: 93.8, test: 93.1 },
    { epoch: 25, train: 96.7, validation: 95.2, test: 94.7 }
  ]);

  const [learningMetrics, setLearningMetrics] = useState({
    currentAccuracy: 94.7,
    targetAccuracy: 97.0,
    improvementRate: 12.3,
    retrainingCycles: 47,
    datasetSize: '2.4M',
    lastRetrain: '2 hours ago',
    nextRetrain: 'In 4 hours',
    modelVersion: 'v2.47.3'
  });

  const [skillRadar, setSkillRadar] = useState([
    { skill: 'Pattern Recognition', current: 95, target: 98 },
    { skill: 'Decision Making', current: 92, target: 95 },
    { skill: 'Reasoning', current: 94, target: 97 },
    { skill: 'Context Understanding', current: 89, target: 93 },
    { skill: 'Error Recovery', current: 91, target: 94 },
    { skill: 'Adaptability', current: 87, target: 92 }
  ]);

  const [retrainingHistory, setRetrainingHistory] = useState([
    { cycle: 43, trigger: 'Performance Drop', duration: '24 min', improvement: '+2.3%', status: 'success' },
    { cycle: 44, trigger: 'Scheduled', duration: '28 min', improvement: '+1.7%', status: 'success' },
    { cycle: 45, trigger: 'New Data', duration: '31 min', improvement: '+3.1%', status: 'success' },
    { cycle: 46, trigger: 'Manual', duration: '26 min', improvement: '+1.2%', status: 'success' },
    { cycle: 47, trigger: 'Performance Drop', duration: '29 min', improvement: '+2.8%', status: 'success' }
  ]);

  const [dataQuality, setDataQuality] = useState([
    { month: 'Jan', quality: 87.2, volume: 342000, accuracy: 91.5 },
    { month: 'Feb', quality: 89.5, volume: 389000, accuracy: 92.8 },
    { month: 'Mar', quality: 91.3, volume: 421000, accuracy: 93.9 },
    { month: 'Apr', quality: 92.7, volume: 456000, accuracy: 94.3 },
    { month: 'May', quality: 93.9, volume: 489000, accuracy: 94.9 },
    { month: 'Jun', quality: 94.8, volume: 523000, accuracy: 95.7 }
  ]);

  return (
    <div className="space-y-6">
      {/* Simulated Data Notice */}
      <Card className="bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 bg-amber-500 rounded-full"></div>
            <p className="text-sm font-medium text-slate-900">
              <strong>Demo Mode:</strong> Learning analytics displayed are simulated examples. Real training data and metrics will populate when connected to live ML pipelines.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Learning Overview Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <Brain className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Current</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Model Accuracy</p>
            <p className="text-4xl font-bold">{learningMetrics.currentAccuracy}%</p>
            <p className="text-xs opacity-75 mt-2">Target: {learningMetrics.targetAccuracy}%</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <TrendingUp className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Growth</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Improvement Rate</p>
            <p className="text-4xl font-bold">+{learningMetrics.improvementRate}%</p>
            <p className="text-xs opacity-75 mt-2">vs. baseline model</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <RefreshCw className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Cycles</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Retraining Cycles</p>
            <p className="text-4xl font-bold">{learningMetrics.retrainingCycles}</p>
            <p className="text-xs opacity-75 mt-2">Last: {learningMetrics.lastRetrain}</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-500 to-orange-600 text-white">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-3">
              <BookOpen className="w-8 h-8 opacity-80" />
              <Badge className="bg-white/20 text-white border-0">Data</Badge>
            </div>
            <p className="text-sm opacity-90 mb-1">Training Dataset</p>
            <p className="text-4xl font-bold">{learningMetrics.datasetSize}</p>
            <p className="text-xs opacity-75 mt-2">samples collected</p>
          </CardContent>
        </Card>
      </div>

      {/* Accuracy Evolution */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Model Accuracy Evolution
          </CardTitle>
          <CardDescription>Training, validation, and test accuracy across epochs</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={accuracyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="epoch" stroke="#64748b" label={{ value: 'Epoch', position: 'insideBottom', offset: -5 }} />
              <YAxis stroke="#64748b" domain={[70, 100]} label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(255, 255, 255, 0.95)', 
                  border: '1px solid #e2e8f0',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }} 
              />
              <Legend />
              <Line type="monotone" dataKey="train" stroke="#3b82f6" strokeWidth={2} name="Training" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="validation" stroke="#10b981" strokeWidth={2} name="Validation" dot={{ r: 4 }} />
              <Line type="monotone" dataKey="test" stroke="#f59e0b" strokeWidth={2} name="Test" dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Skill Analysis & Retraining History */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5 text-purple-600" />
              Skill Assessment Radar
            </CardTitle>
            <CardDescription>Current performance vs. target benchmarks</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={skillRadar}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="skill" tick={{ fontSize: 12, fill: '#64748b' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: '#64748b' }} />
                <Radar name="Current" dataKey="current" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.5} />
                <Radar name="Target" dataKey="target" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-green-600" />
              Recent Retraining Cycles
            </CardTitle>
            <CardDescription>Autonomous retraining history and performance gains</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {retrainingHistory.map((cycle, index) => (
                <div key={index} className="p-4 border border-slate-200 rounded-lg hover:border-blue-300 transition-colors">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge className="bg-blue-100 text-blue-700 border-0">
                        Cycle #{cycle.cycle}
                      </Badge>
                      <span className="text-sm font-medium text-slate-700">{cycle.trigger}</span>
                    </div>
                    <Badge className="bg-green-100 text-green-700 border-0">
                      {cycle.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Duration</p>
                      <p className="font-semibold text-slate-900">{cycle.duration}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Improvement</p>
                      <p className="font-semibold text-green-600 flex items-center gap-1">
                        <ArrowUpRight className="w-4 h-4" />
                        {cycle.improvement}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Data Quality Trends */}
      <Card className="bg-white/80 backdrop-blur-sm border-slate-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="w-5 h-5 text-orange-600" />
            Training Data Quality & Volume Analysis
          </CardTitle>
          <CardDescription>Correlation between data quality, volume, and model performance</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={dataQuality}>
              <defs>
                <linearGradient id="colorQuality" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorAccuracy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" stroke="#64748b" />
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
              <Area type="monotone" dataKey="quality" stroke="#3b82f6" fillOpacity={1} fill="url(#colorQuality)" name="Data Quality (%)" />
              <Area type="monotone" dataKey="accuracy" stroke="#10b981" fillOpacity={1} fill="url(#colorAccuracy)" name="Model Accuracy (%)" />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
