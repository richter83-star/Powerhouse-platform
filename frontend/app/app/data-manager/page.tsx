
"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useToast } from "@/hooks/use-toast";
import {
  Upload,
  Download,
  FileText,
  Trash2,
  FolderOpen,
  Copy,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  FileJson,
  File,
  FileCog,
  Database,
  TrendingUp,
} from "lucide-react";
import { motion } from "framer-motion";
import { API_ENDPOINTS } from "@/lib/api-config";

interface FileItem {
  id: string;
  name: string;
  size: number;
  modified_at?: string;
  uploaded_at?: string;
  type: string;
  mime_type?: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  filename: string;
}

interface FileStats {
  uploads: { size: number; count: number };
  outputs: { size: number; count: number };
  templates: { size: number; count: number };
  samples: { size: number; count: number };
  total_size: number;
  total_count: number;
}

export default function DataManagerPage() {
  const [activeTab, setActiveTab] = useState("upload");
  const [files, setFiles] = useState<FileItem[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [samples, setSamples] = useState<FileItem[]>([]);
  const [outputs, setOutputs] = useState<FileItem[]>([]);
  const [stats, setStats] = useState<FileStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const { toast } = useToast();

  const API_BASE = API_ENDPOINTS.files;

  // Fetch files based on type
  const fetchFiles = useCallback(async (type: string) => {
    try {
      const response = await fetch(`${API_BASE}/files?file_type=${type}`);
      const data = await response.json();
      if (data.success) {
        switch (type) {
          case "uploads":
            setFiles(data.files || []);
            break;
          case "outputs":
            setOutputs(data.files || []);
            break;
          case "samples":
            setSamples(data.files || []);
            break;
        }
      }
    } catch (error) {
      console.error(`Error fetching ${type}:`, error);
    }
  }, []);

  // Fetch templates
  const fetchTemplates = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/templates/list`);
      const data = await response.json();
      if (data.success) {
        setTemplates(data.templates || []);
      }
    } catch (error) {
      console.error("Error fetching templates:", error);
    }
  }, []);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      const data = await response.json();
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchFiles("uploads");
    fetchFiles("outputs");
    fetchFiles("samples");
    fetchTemplates();
    fetchStats();
  }, [fetchFiles, fetchTemplates, fetchStats]);

  // Handle file upload
  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      toast({
        title: "No files selected",
        description: "Please select files to upload",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      Array.from(selectedFiles).forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (data.success) {
        toast({
          title: "Upload successful",
          description: `${data.files.length} file(s) uploaded successfully`,
        });
        fetchFiles("uploads");
        fetchStats();
        setSelectedFiles(null);
        // Reset file input
        const fileInput = document.getElementById("file-input") as HTMLInputElement;
        if (fileInput) fileInput.value = "";
      }
    } catch (error) {
      toast({
        title: "Upload failed",
        description: "Failed to upload files. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle file download
  const handleDownload = async (type: string, filename: string) => {
    try {
      const response = await fetch(`${API_BASE}/download/${type}/${filename}`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      toast({
        title: "Download failed",
        description: "Failed to download file",
        variant: "destructive",
      });
    }
  };

  // Handle file delete
  const handleDelete = async (type: string, filename: string) => {
    try {
      const response = await fetch(`${API_BASE}/delete/${type}/${filename}`, {
        method: "DELETE",
      });
      const data = await response.json();
      if (data.success) {
        toast({
          title: "File deleted",
          description: data.message,
        });
        fetchFiles(type);
        fetchStats();
      }
    } catch (error) {
      toast({
        title: "Delete failed",
        description: "Failed to delete file",
        variant: "destructive",
      });
    }
  };

  // Handle template download
  const handleTemplateDownload = async (filename: string) => {
    try {
      const response = await fetch(`${API_BASE}/templates/${filename}`);
      const data = await response.json();
      if (data.success) {
        const blob = new Blob([JSON.stringify(data.template, null, 2)], {
          type: "application/json",
        });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      toast({
        title: "Download failed",
        description: "Failed to download template",
        variant: "destructive",
      });
    }
  };

  // Drag and drop handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(e.dataTransfer.files);
    }
  };

  // Format file size
  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  // Get file icon
  const getFileIcon = (filename: string) => {
    if (filename.endsWith(".json")) return <FileJson className="h-4 w-4" />;
    if (filename.endsWith(".csv")) return <Database className="h-4 w-4" />;
    return <File className="h-4 w-4" />;
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Manager</h1>
          <p className="text-muted-foreground mt-1">
            Manage inputs, outputs, templates, and test materials
          </p>
        </div>
        <Button onClick={() => {
          fetchFiles("uploads");
          fetchFiles("outputs");
          fetchFiles("samples");
          fetchTemplates();
          fetchStats();
        }}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh All
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Total Files</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_count}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {formatSize(stats.total_size)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Uploads</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.uploads.count}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {formatSize(stats.uploads.size)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Outputs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.outputs.count}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {formatSize(stats.outputs.size)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.templates.count}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats.samples.count} samples
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upload">
            <Upload className="h-4 w-4 mr-2" />
            Upload
          </TabsTrigger>
          <TabsTrigger value="templates">
            <FileCog className="h-4 w-4 mr-2" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="samples">
            <Database className="h-4 w-4 mr-2" />
            Samples
          </TabsTrigger>
          <TabsTrigger value="outputs">
            <TrendingUp className="h-4 w-4 mr-2" />
            Outputs
          </TabsTrigger>
        </TabsList>

        {/* Upload Tab */}
        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload Files</CardTitle>
              <CardDescription>
                Upload input files for processing. Supports JSON, CSV, TXT, and other formats.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Drag and Drop Area */}
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive
                    ? "border-primary bg-primary/5"
                    : "border-muted-foreground/25 hover:border-muted-foreground/50"
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Upload className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">
                  Drop files here or click to browse
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Supports all file types
                </p>
                <Input
                  id="file-input"
                  type="file"
                  multiple
                  className="hidden"
                  onChange={(e) => setSelectedFiles(e.target.files)}
                />
                <Button
                  variant="outline"
                  onClick={() => document.getElementById("file-input")?.click()}
                >
                  <FolderOpen className="h-4 w-4 mr-2" />
                  Browse Files
                </Button>
              </div>

              {/* Selected Files */}
              {selectedFiles && selectedFiles.length > 0 && (
                <div className="space-y-2">
                  <Label>Selected Files ({selectedFiles.length})</Label>
                  <ScrollArea className="h-32 border rounded-md p-2">
                    {Array.from(selectedFiles).map((file, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between py-1 px-2 hover:bg-muted/50 rounded"
                      >
                        <span className="text-sm">{file.name}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatSize(file.size)}
                        </span>
                      </div>
                    ))}
                  </ScrollArea>
                  <Button
                    onClick={handleUpload}
                    disabled={loading}
                    className="w-full"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload {selectedFiles.length} File(s)
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Uploaded Files List */}
          <Card>
            <CardHeader>
              <CardTitle>Your Uploads</CardTitle>
              <CardDescription>Recently uploaded files</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                {files.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <FileText className="h-12 w-12 mx-auto mb-2 opacity-20" />
                    <p>No files uploaded yet</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {files.map((file) => (
                      <motion.div
                        key={file.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                      >
                        <div className="flex items-center space-x-3">
                          {getFileIcon(file.name)}
                          <div>
                            <p className="text-sm font-medium">{file.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatSize(file.size)} •{" "}
                              {new Date(file.modified_at || "").toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload("uploads", file.name)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete("uploads", file.name)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {templates.map((template) => (
              <Card key={template.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg">{template.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {template.description}
                      </CardDescription>
                    </div>
                    <Badge variant="secondary">{template.category}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => handleTemplateDownload(template.filename)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1"
                      onClick={() => {
                        navigator.clipboard.writeText(template.filename);
                        toast({ title: "Copied to clipboard" });
                      }}
                    >
                      <Copy className="h-4 w-4 mr-2" />
                      Copy ID
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Samples Tab */}
        <TabsContent value="samples" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Sample Files</CardTitle>
              <CardDescription>
                Example input files to help you get started
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                {samples.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Database className="h-12 w-12 mx-auto mb-2 opacity-20" />
                    <p>No sample files available</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {samples.map((sample) => (
                      <div
                        key={sample.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                      >
                        <div className="flex items-center space-x-3">
                          {getFileIcon(sample.name)}
                          <div>
                            <p className="text-sm font-medium">{sample.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatSize(sample.size)}
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownload("samples", sample.name)}
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Download
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Outputs Tab */}
        <TabsContent value="outputs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Generated Outputs</CardTitle>
              <CardDescription>Results from your processing tasks</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                {outputs.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <TrendingUp className="h-12 w-12 mx-auto mb-2 opacity-20" />
                    <p>No outputs generated yet</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {outputs.map((output) => (
                      <div
                        key={output.id}
                        className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50"
                      >
                        <div className="flex items-center space-x-3">
                          {getFileIcon(output.name)}
                          <div>
                            <p className="text-sm font-medium">{output.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {formatSize(output.size)} •{" "}
                              {new Date(output.modified_at || "").toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDownload("outputs", output.name)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDelete("outputs", output.name)}
                          >
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Button variant="outline" className="h-auto py-4 flex-col">
            <CheckCircle2 className="h-8 w-8 mb-2 text-green-500" />
            <span className="font-semibold">View Documentation</span>
            <span className="text-xs text-muted-foreground mt-1">
              Learn about file formats
            </span>
          </Button>
          <Button
            variant="outline"
            className="h-auto py-4 flex-col"
            onClick={() => setActiveTab("templates")}
          >
            <FileCog className="h-8 w-8 mb-2 text-blue-500" />
            <span className="font-semibold">Browse Templates</span>
            <span className="text-xs text-muted-foreground mt-1">
              Pre-built task configurations
            </span>
          </Button>
          <Button
            variant="outline"
            className="h-auto py-4 flex-col"
            onClick={() => setActiveTab("samples")}
          >
            <Database className="h-8 w-8 mb-2 text-purple-500" />
            <span className="font-semibold">Download Samples</span>
            <span className="text-xs text-muted-foreground mt-1">
              Example input files
            </span>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
