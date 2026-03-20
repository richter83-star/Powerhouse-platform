'use client';

import { useState, useEffect, useRef } from 'react';
import { useStreamingRun, AgentOutput } from '@/hooks/use-streaming-run';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Play,
  Square,
  RotateCcw,
  Copy,
  Download,
  CheckCircle2,
  XCircle,
  Loader2,
  Terminal,
  Clock,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const MAX_TASK_LENGTH = 10_000;

interface RunHistoryEntry {
  id: string;
  task: string;
  outputs: AgentOutput[];
  completedAt: number;
  durationMs: number;
}

function loadHistory(): RunHistoryEntry[] {
  if (typeof window === 'undefined') return [];
  try {
    return JSON.parse(localStorage.getItem('ph_run_history') || '[]');
  } catch {
    return [];
  }
}

function saveHistory(entries: RunHistoryEntry[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem('ph_run_history', JSON.stringify(entries.slice(0, 10)));
}

export function AgentRunPanel() {
  const [task, setTask] = useState('');
  const [copied, setCopied] = useState(false);
  const [history, setHistory] = useState<RunHistoryEntry[]>([]);
  const startTimeRef = useRef<number>(0);
  const { outputs, isRunning, error, startRun, stopRun, reset } = useStreamingRun();

  useEffect(() => {
    setHistory(loadHistory());
  }, []);

  const handleRun = () => {
    if (!task.trim() || isRunning) return;
    startTimeRef.current = Date.now();
    startRun(task.trim());
  };

  const handleStop = () => stopRun();

  const handleReset = () => {
    reset();
    setTask('');
  };

  // Save completed run to history
  useEffect(() => {
    if (!isRunning && outputs.length > 0 && startTimeRef.current > 0) {
      const entry: RunHistoryEntry = {
        id: `run-${Date.now()}`,
        task,
        outputs,
        completedAt: Date.now(),
        durationMs: Date.now() - startTimeRef.current,
      };
      const updated = [entry, ...loadHistory()].slice(0, 10);
      saveHistory(updated);
      setHistory(updated);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isRunning]);

  const handleCopyAll = async () => {
    const text = outputs.map(o => `## ${o.agent}\n${o.output}`).join('\n\n');
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const data = JSON.stringify({ task, outputs, exportedAt: new Date().toISOString() }, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `powerhouse-run-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const doneCount = outputs.filter(o => o.status === 'done' || o.status === 'error').length;
  const progressPct = outputs.length > 0 ? (doneCount / outputs.length) * 100 : 0;
  const hasResults = outputs.length > 0;

  return (
    <div className="space-y-6">
      {/* Input Panel */}
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Terminal className="w-5 h-5 text-primary" />
            Run Agent Task
          </CardTitle>
          <CardDescription>
            Describe your task and the multi-agent pipeline will execute it in real-time.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Textarea
              placeholder="Describe your task… e.g. 'Analyze the latest market trends in renewable energy and produce a structured report with key findings.'"
              value={task}
              onChange={e => setTask(e.target.value.slice(0, MAX_TASK_LENGTH))}
              className="min-h-[120px] resize-y font-mono text-sm bg-background/50"
              disabled={isRunning}
              aria-label="Task description"
            />
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>{task.length.toLocaleString()} / {MAX_TASK_LENGTH.toLocaleString()} chars</span>
              {task.length > MAX_TASK_LENGTH * 0.9 && (
                <span className="text-yellow-500">Approaching character limit</span>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {!isRunning ? (
              <Button
                onClick={handleRun}
                disabled={!task.trim()}
                className="gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
              >
                <Play className="w-4 h-4" />
                Run Pipeline
              </Button>
            ) : (
              <Button onClick={handleStop} variant="destructive" className="gap-2">
                <Square className="w-4 h-4" />
                Stop
              </Button>
            )}
            {hasResults && !isRunning && (
              <>
                <Button onClick={handleCopyAll} variant="outline" size="sm" className="gap-2">
                  <Copy className="w-4 h-4" />
                  {copied ? 'Copied!' : 'Copy All'}
                </Button>
                <Button onClick={handleDownload} variant="outline" size="sm" className="gap-2">
                  <Download className="w-4 h-4" />
                  Download
                </Button>
                <Button onClick={handleReset} variant="ghost" size="sm" className="gap-2 ml-auto">
                  <RotateCcw className="w-4 h-4" />
                  New Run
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Error Banner */}
      {error && (
        <div
          className="flex items-start gap-3 p-4 rounded-lg border border-destructive/50 bg-destructive/10 text-destructive text-sm"
          role="alert"
          aria-live="assertive"
        >
          <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Pipeline error</p>
            <p className="opacity-90 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Live Progress */}
      {(isRunning || hasResults) && (
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                {isRunning ? (
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                ) : (
                  <Sparkles className="w-4 h-4 text-primary" />
                )}
                {isRunning ? 'Pipeline Running…' : 'Pipeline Complete'}
              </CardTitle>
              {hasResults && (
                <span className="text-sm text-muted-foreground">
                  {doneCount} / {outputs.length} agents
                </span>
              )}
            </div>
            {hasResults && (
              <Progress value={isRunning ? undefined : progressPct} className="h-2 mt-2" />
            )}
          </CardHeader>
          <CardContent>
            {isRunning && outputs.length === 0 && (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="flex items-center gap-3">
                    <Skeleton className="h-4 w-4 rounded-full" />
                    <Skeleton className="h-4 flex-1" />
                  </div>
                ))}
              </div>
            )}

            <Accordion type="multiple" className="space-y-2">
              {outputs.map(output => (
                <AgentOutputCard key={output.agent} output={output} />
              ))}
            </Accordion>
          </CardContent>
        </Card>
      )}

      {/* Run History */}
      {history.length > 0 && (
        <Card className="border-border/30 bg-card/30">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-base text-muted-foreground">
              <Clock className="w-4 h-4" />
              Recent Runs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {history.map(entry => {
                const successCount = entry.outputs.filter(o => o.status === 'done').length;
                const failCount = entry.outputs.filter(o => o.status === 'error').length;
                return (
                  <div
                    key={entry.id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-border/30 hover:bg-accent/30 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{entry.task}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {new Date(entry.completedAt).toLocaleString()} ·{' '}
                        {(entry.durationMs / 1000).toFixed(1)}s
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {successCount > 0 && (
                        <Badge variant="secondary" className="text-xs bg-green-500/20 text-green-400 border-green-500/30">
                          {successCount} ok
                        </Badge>
                      )}
                      {failCount > 0 && (
                        <Badge variant="destructive" className="text-xs">
                          {failCount} err
                        </Badge>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function AgentOutputCard({ output }: { output: AgentOutput }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(output.output);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <AccordionItem
      value={output.agent}
      className={cn(
        'border rounded-lg px-4',
        output.status === 'error'
          ? 'border-destructive/40 bg-destructive/5'
          : output.status === 'done'
          ? 'border-green-500/30 bg-green-500/5'
          : 'border-border/40 bg-card/30'
      )}
    >
      <AccordionTrigger className="hover:no-underline py-3">
        <div className="flex items-center gap-3 w-full">
          {output.status === 'running' ? (
            <Loader2 className="w-4 h-4 animate-spin text-primary flex-shrink-0" />
          ) : output.status === 'error' ? (
            <XCircle className="w-4 h-4 text-destructive flex-shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
          )}
          <span className="font-mono text-sm font-semibold capitalize">
            {output.agent.replace(/_/g, ' ')}
          </span>
          <Badge
            variant="outline"
            className={cn(
              'text-xs ml-auto mr-2',
              output.status === 'error'
                ? 'border-destructive/50 text-destructive'
                : output.status === 'done'
                ? 'border-green-500/50 text-green-400'
                : 'border-border text-muted-foreground'
            )}
          >
            {output.status}
          </Badge>
        </div>
      </AccordionTrigger>
      <AccordionContent className="pb-3">
        <div className="relative">
          <pre className="text-xs font-mono whitespace-pre-wrap bg-background/50 rounded-md p-3 overflow-auto max-h-80 text-foreground/90">
            {output.output || '(no output)'}
          </pre>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="absolute top-2 right-2 h-7 w-7 p-0 opacity-60 hover:opacity-100"
            aria-label={`Copy ${output.agent} output`}
          >
            <Copy className="w-3 h-3" />
          </Button>
        </div>
        {copied && (
          <p className="text-xs text-muted-foreground mt-1">Copied to clipboard</p>
        )}
      </AccordionContent>
    </AccordionItem>
  );
}
