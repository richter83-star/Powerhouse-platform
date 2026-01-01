"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
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
  ResponsiveContainer
} from "recharts";
import {
  GitBranch,
  TrendingUp,
  Database,
  Brain,
  Activity,
  RotateCcw,
  Sparkles,
  AlertCircle
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

interface TrendPoint {
  period: string;
  accuracy?: number;
  latency?: number;
}

export default function AIQualityPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [qualityTrends, setQualityTrends] = useState<TrendPoint[]>([]);
  const [featureImportance, setFeatureImportance] = useState<{ feature: string; importance: number }[]>([]);
  const [decisionPatterns, setDecisionPatterns] = useState<any | null>(null);
  const [modelId, setModelId] = useState("");
  const [modelLoading, setModelLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const results = await Promise.allSettled([
        fetch(`${apiUrl}/ai-quality/stats`),
        fetch(`${apiUrl}/ai-quality/datasets`),
        fetch(`${apiUrl}/ai-quality/metrics/accuracy/trends`),
        fetch(`${apiUrl}/ai-quality/metrics/latency/trends`)
      ]);

      const statsRes = results[0].status === "fulfilled" ? results[0].value : null;
      const datasetsRes = results[1].status === "fulfilled" ? results[1].value : null;
      const accuracyRes = results[2].status === "fulfilled" ? results[2].value : null;
      const latencyRes = results[3].status === "fulfilled" ? results[3].value : null;

      if (statsRes?.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      if (datasetsRes?.ok) {
        const datasetsData = await datasetsRes.json();
        setDatasets(datasetsData.datasets || []);
      }

      let accuracyTrends: any[] = [];
      let latencyTrends: any[] = [];

      if (accuracyRes?.ok) {
        const accuracyData = await accuracyRes.json();
        accuracyTrends = accuracyData?.trends || [];
      }
      if (latencyRes?.ok) {
        const latencyData = await latencyRes.json();
        latencyTrends = latencyData?.trends || [];
      }

      const baseTrends = accuracyTrends.length ? accuracyTrends : latencyTrends;
      if (baseTrends.length > 0) {
        const merged = baseTrends.map((point, idx) => ({
          period: new Date(point.period).toLocaleTimeString(),
          accuracy: accuracyTrends[idx]?.value ?? 0,
          latency: latencyTrends[idx]?.value ?? 0
        }));
        setQualityTrends(merged);
      } else {
        setQualityTrends([]);
      }
    } catch (error) {
      console.error("Error fetching AI quality data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchModelDetails = async () => {
    if (!modelId.trim()) {
      return;
    }

    setModelLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const results = await Promise.allSettled([
        fetch(`${apiUrl}/ai-quality/models/${modelId}/versions`),
        fetch(`${apiUrl}/ai-quality/models/${modelId}/feature-importance`),
        fetch(`${apiUrl}/ai-quality/models/${modelId}/decision-patterns`)
      ]);

      const versionsRes = results[0].status === "fulfilled" ? results[0].value : null;
      const importanceRes = results[1].status === "fulfilled" ? results[1].value : null;
      const patternsRes = results[2].status === "fulfilled" ? results[2].value : null;

      if (versionsRes?.ok) {
        const versionsData = await versionsRes.json();
        setModels(versionsData?.versions || []);
      } else {
        setModels([]);
      }

      if (importanceRes?.ok) {
        const importanceData = await importanceRes.json();
        const features = importanceData?.feature_importance || {};
        const entries = Object.entries(features).map(([feature, value]) => ({
          feature,
          importance: Number(value)
        }));
        setFeatureImportance(entries);
      } else {
        setFeatureImportance([]);
      }

      if (patternsRes?.ok) {
        const patternsData = await patternsRes.json();
        setDecisionPatterns(patternsData?.error ? null : patternsData);
      } else {
        setDecisionPatterns(null);
      }
    } catch (error) {
      console.error("Error fetching model details:", error);
      setModels([]);
      setFeatureImportance([]);
      setDecisionPatterns(null);
    } finally {
      setModelLoading(false);
    }
  };

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
            <Card className="col-span-1">
              <CardHeader>
                <CardTitle>Quality Trends</CardTitle>
                <CardDescription>Accuracy and latency trends</CardDescription>
              </CardHeader>
              <CardContent>
                {qualityTrends.length === 0 ? (
                  <div className="text-sm text-muted-foreground">No quality trend data available.</div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={qualityTrends}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="period" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="accuracy" stroke="#10b981" strokeWidth={2} />
                      <Line type="monotone" dataKey="latency" stroke="#f59e0b" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>

            <Card className="col-span-1">
              <CardHeader>
                <CardTitle>Feature Importance</CardTitle>
                <CardDescription>Top factors influencing predictions</CardDescription>
              </CardHeader>
              <CardContent>
                {featureImportance.length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    Load a model to view feature importance.
                  </div>
                ) : (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={featureImportance} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis type="number" />
                      <YAxis dataKey="feature" type="category" width={150} />
                      <Tooltip />
                      <Bar dataKey="importance" fill="#8b5cf6" />
                    </BarChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Model Comparison</CardTitle>
              <CardDescription>Use A/B tests to compare model versions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                No active A/B test summaries available. Create an A/B test to compare model performance.
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Versions Tab */}
        <TabsContent value="versions" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Versions</CardTitle>
              <CardDescription>Load a model ID to view registered versions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col md:flex-row gap-2">
                <Input
                  placeholder="Enter model ID (e.g. compliance-model)"
                  value={modelId}
                  onChange={(event) => setModelId(event.target.value)}
                />
                <Button onClick={fetchModelDetails} disabled={!modelId || modelLoading}>
                  {modelLoading ? "Loading..." : "Load Model"}
                </Button>
              </div>

              {models.length > 0 ? (
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
                          {Object.entries(model.metrics || {}).slice(0, 2).map(([key, value]) => (
                            <span key={key}>{key}: {value}</span>
                          ))}
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(model.created_at).toLocaleString()}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No versions loaded</p>
                  <p className="text-sm">Enter a model ID to retrieve versions</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Quality Tab */}
        <TabsContent value="quality" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Quality Metrics</CardTitle>
              <CardDescription>Quality metrics are recorded via the metrics collector</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-start gap-3 p-3 bg-yellow-50 dark:bg-yellow-950 rounded-lg">
                <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">No detailed quality breakdown available</p>
                  <p className="text-xs text-muted-foreground">
                    Record accuracy, latency, and relevance metrics to populate this view.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
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
                {featureImportance.length === 0 ? (
                  <div className="text-sm text-muted-foreground">
                    Load a model ID to access explainability metrics.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {featureImportance.slice(0, 6).map((item) => (
                      <div key={item.feature} className="flex justify-between text-sm">
                        <span className="text-muted-foreground">{item.feature}</span>
                        <span className="font-medium">{(item.importance * 100).toFixed(1)}%</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Decision Patterns</CardTitle>
                <CardDescription>Analysis of model behavior</CardDescription>
              </CardHeader>
              <CardContent>
                {decisionPatterns ? (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Explanations</span>
                      <span className="font-medium">{decisionPatterns.total_explanations}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Avg Confidence</span>
                      <span className="font-medium">
                        {(decisionPatterns.average_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Top Features</p>
                      {Object.entries(decisionPatterns.top_features || {}).slice(0, 5).map(([feature, value]) => (
                        <div key={feature} className="flex justify-between text-xs">
                          <span>{feature}</span>
                          <span>{(Number(value) * 100).toFixed(1)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">
                    No decision pattern analysis available for this model.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
