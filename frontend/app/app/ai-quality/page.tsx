
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  LineChart, 
  Line, 
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
} from "recharts";
import {
  GitBranch,
  TrendingUp,
  Database,
  Brain,
  Activity,
  CheckCircle2,
  AlertCircle,
  ArrowUpRight,
  Play,
  RotateCcw,
  Sparkles
} from "lucide-react";

interface Stats {
  versioning: {
    total_models: number;
    total_versions: number;
    active_ab_tests: number;
  };
  metrics: {
    total_metric_types: number;
    total_data_points: number;
  };
  training_data: {
    total_datasets: number;
    total_versions: number;
    average_quality_score: number;
  };
  explainability: {
    models_with_explanations: number;
    total_explanations: number;
  };
}

interface ModelVersion {
  model_id: string;
  version: string;
  created_at: string;
  metrics: Record<string, number>;
  status: string;
}

interface Dataset {
  dataset_id: string;
  latest_version: string;
  total_versions: number;
  quality_score: number;
}

export default function AIQualityPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch stats
      const statsRes = await fetch("http://localhost:8000/ai-quality/stats");
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // Fetch datasets
      const datasetsRes = await fetch("http://localhost:8000/ai-quality/datasets");
      if (datasetsRes.ok) {
        const datasetsData = await datasetsRes.json();
        setDatasets(datasetsData.datasets || []);
      }

      // Simulate some model versions for demo
      setModels([
        {
          model_id: "gpt-compliance-v1",
          version: "2.4.1",
          created_at: new Date().toISOString(),
          metrics: { accuracy: 0.94, latency: 125 },
          status: "active"
        },
        {
          model_id: "claude-analyzer",
          version: "1.8.3",
          created_at: new Date(Date.now() - 86400000).toISOString(),
          metrics: { accuracy: 0.91, latency: 98 },
          status: "testing"
        },
        {
          model_id: "bert-classifier",
          version: "3.2.0",
          created_at: new Date(Date.now() - 172800000).toISOString(),
          metrics: { accuracy: 0.89, latency: 45 },
          status: "archived"
        }
      ]);

    } catch (error) {
      console.error("Error fetching AI quality data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Mock data for charts
  const qualityTrends = [
    { period: "Week 1", accuracy: 0.85, latency: 150, quality_score: 78 },
    { period: "Week 2", accuracy: 0.87, latency: 145, quality_score: 82 },
    { period: "Week 3", accuracy: 0.89, latency: 138, quality_score: 85 },
    { period: "Week 4", accuracy: 0.92, latency: 125, quality_score: 89 },
    { period: "Week 5", accuracy: 0.94, latency: 115, quality_score: 92 }
  ];

  const featureImportance = [
    { feature: "document_length", importance: 0.28 },
    { feature: "keyword_density", importance: 0.22 },
    { feature: "clause_complexity", importance: 0.18 },
    { feature: "entity_count", importance: 0.15 },
    { feature: "readability_score", importance: 0.10 },
    { feature: "sentiment", importance: 0.07 }
  ];

  const modelComparison = [
    { metric: "Accuracy", modelA: 0.92, modelB: 0.94 },
    { metric: "Precision", modelA: 0.89, modelB: 0.91 },
    { metric: "Recall", modelA: 0.90, modelB: 0.93 },
    { metric: "F1-Score", modelA: 0.895, modelB: 0.92 },
    { metric: "Latency", modelA: 135, modelB: 125 }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Sparkles className="h-12 w-12 animate-pulse mx-auto mb-4 text-primary" />
          <p className="text-muted-foreground">Loading AI Quality Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-4xl font-bold mb-2">AI Quality Management</h1>
          <p className="text-muted-foreground">
            Enterprise-grade model versioning, quality metrics, and explainability
          </p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <RotateCcw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Model Versions</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.versioning.total_versions || 0}</div>
            <p className="text-xs text-muted-foreground">
              Across {stats?.versioning.total_models || 0} models
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Quality Metrics</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.metrics.total_data_points?.toLocaleString() || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              {stats?.metrics.total_metric_types || 0} metric types tracked
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Training Datasets</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.training_data.total_datasets || 0}</div>
            <p className="text-xs text-muted-foreground">
              Avg quality: {((stats?.training_data.average_quality_score || 0) * 100).toFixed(0)}%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">A/B Tests</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.versioning.active_ab_tests || 0}</div>
            <p className="text-xs text-muted-foreground">Active experiments</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="versions">Versions</TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
          <TabsTrigger value="datasets">Datasets</TabsTrigger>
          <TabsTrigger value="explainability">Explainability</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Quality Trends */}
            <Card className="col-span-1">
              <CardHeader>
                <CardTitle>Quality Trends</CardTitle>
                <CardDescription>Model performance over time</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={qualityTrends}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="quality_score" stroke="#8b5cf6" strokeWidth={2} />
                    <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Feature Importance */}
            <Card className="col-span-1">
              <CardHeader>
                <CardTitle>Feature Importance</CardTitle>
                <CardDescription>Top factors influencing predictions</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={featureImportance} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="feature" type="category" width={150} />
                    <Tooltip />
                    <Bar dataKey="importance" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Model Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>A/B Test: Model Comparison</CardTitle>
              <CardDescription>Comparing gpt-compliance-v1 v2.3 vs v2.4</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={modelComparison}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis />
                  <Radar name="Model A (v2.3)" dataKey="modelA" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                  <Radar name="Model B (v2.4)" dataKey="modelB" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Versions Tab */}
        <TabsContent value="versions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Versions</CardTitle>
              <CardDescription>Manage and track model versions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {models.map((model, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{model.model_id}</h3>
                        <Badge variant={model.status === "active" ? "default" : "secondary"}>
                          {model.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">Version {model.version}</p>
                      <div className="flex gap-4 mt-2 text-sm">
                        <span>Accuracy: {(model.metrics.accuracy * 100).toFixed(1)}%</span>
                        <span>Latency: {model.metrics.latency}ms</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {model.status !== "active" && (
                        <Button size="sm" variant="outline">
                          <Play className="h-4 w-4 mr-1" />
                          Activate
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        <RotateCcw className="h-4 w-4 mr-1" />
                        Rollback
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Quality Dimensions</CardTitle>
                <CardDescription>Comprehensive quality assessment</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { name: "Accuracy", score: 94, status: "excellent" },
                    { name: "Relevance", score: 89, status: "good" },
                    { name: "Coherence", score: 92, status: "excellent" },
                    { name: "Completeness", score: 87, status: "good" },
                    { name: "Latency", score: 78, status: "fair" },
                    { name: "Error Rate", score: 95, status: "excellent" }
                  ].map((dim, idx) => (
                    <div key={idx} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{dim.name}</span>
                        <span className="font-medium">{dim.score}%</span>
                      </div>
                      <div className="h-2 bg-secondary rounded-full overflow-hidden">
                        <div
                          className={`h-full ${
                            dim.status === "excellent"
                              ? "bg-green-500"
                              : dim.status === "good"
                              ? "bg-blue-500"
                              : "bg-yellow-500"
                          }`}
                          style={{ width: `${dim.score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Recent Anomalies</CardTitle>
                <CardDescription>Detected quality issues</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg">
                    <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">High latency spike</p>
                      <p className="text-xs text-muted-foreground">
                        Latency exceeded 200ms threshold
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">2 hours ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                    <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">Quality improvement</p>
                      <p className="text-xs text-muted-foreground">
                        Accuracy increased by 3.2%
                      </p>
                      <p className="text-xs text-muted-foreground mt-1">1 day ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Datasets Tab */}
        <TabsContent value="datasets" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Training Datasets</CardTitle>
              <CardDescription>Manage training data quality and versions</CardDescription>
            </CardHeader>
            <CardContent>
              {datasets.length > 0 ? (
                <div className="space-y-4">
                  {datasets.map((dataset, idx) => (
                    <div key={idx} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <h3 className="font-semibold">{dataset.dataset_id}</h3>
                        <p className="text-sm text-muted-foreground">
                          Version {dataset.latest_version} • {dataset.total_versions} versions
                        </p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-sm">Quality Score:</span>
                          <div className="flex-1 max-w-xs h-2 bg-secondary rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary"
                              style={{ width: `${dataset.quality_score * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-medium">
                            {(dataset.quality_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <Button size="sm" variant="outline">
                        View Details
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <Database className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No datasets found</p>
                  <p className="text-sm">Register a dataset to get started</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Explainability Tab */}
        <TabsContent value="explainability" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Model Explainability</CardTitle>
                <CardDescription>Understanding model decisions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Brain className="h-5 w-5 text-primary" />
                      <h4 className="font-medium">Feature Importance</h4>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      SHAP values show which features contribute most to predictions
                    </p>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <ArrowUpRight className="h-5 w-5 text-primary" />
                      <h4 className="font-medium">Counterfactual Analysis</h4>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      What changes would lead to different outcomes
                    </p>
                  </div>

                  <div className="p-4 border rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Activity className="h-5 w-5 text-primary" />
                      <h4 className="font-medium">Attention Visualization</h4>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      See which parts of input received most attention
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Decision Patterns</CardTitle>
                <CardDescription>Analysis of model behavior</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Average Confidence</span>
                      <span className="font-medium">87.3%</span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-primary" style={{ width: "87.3%" }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>Prediction Consistency</span>
                      <span className="font-medium">92.1%</span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div className="h-full bg-green-500" style={{ width: "92.1%" }} />
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <h4 className="text-sm font-medium mb-3">Top Influential Features</h4>
                    <div className="space-y-2">
                      {featureImportance.slice(0, 5).map((feat, idx) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span className="text-muted-foreground">{feat.feature}</span>
                          <span className="font-medium">{(feat.importance * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
