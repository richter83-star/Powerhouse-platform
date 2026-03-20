'use client';

import { useState, useCallback, useRef } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface AgentOutput {
  agent: string;
  output: string;
  status: 'running' | 'done' | 'error';
  timestamp: number;
}

export interface StreamingRunResult {
  outputs: AgentOutput[];
  isRunning: boolean;
  error: string | null;
  startRun: (task: string, agents?: string[], mode?: string) => void;
  stopRun: () => void;
  reset: () => void;
}

export function useStreamingRun(): StreamingRunResult {
  const [outputs, setOutputs] = useState<AgentOutput[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const stopRun = useCallback(() => {
    abortRef.current?.abort();
    setIsRunning(false);
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setOutputs([]);
    setIsRunning(false);
    setError(null);
  }, []);

  const startRun = useCallback(async (task: string, agents?: string[], mode = 'sequential') => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setOutputs([]);
    setError(null);
    setIsRunning(true);

    try {
      const response = await fetch(`${API_BASE}/run/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, agents, mode }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error ${response.status}: ${text}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response stream available');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const raw = line.slice(6).trim();
            if (!raw || raw === '[DONE]') continue;
            try {
              const event = JSON.parse(raw);
              const agentName: string = event.agent ?? event.agent_name ?? 'unknown';
              const output: string = event.output ?? event.result ?? event.message ?? '';
              const isError: boolean = event.error === true || event.status === 'error';

              setOutputs(prev => {
                const existing = prev.findIndex(o => o.agent === agentName);
                const entry: AgentOutput = {
                  agent: agentName,
                  output,
                  status: isError ? 'error' : 'done',
                  timestamp: Date.now(),
                };
                if (existing >= 0) {
                  const next = [...prev];
                  next[existing] = entry;
                  return next;
                }
                return [...prev, entry];
              });
            } catch {
              // non-JSON SSE line — skip
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      setError(err instanceof Error ? err.message : 'Unexpected error');
    } finally {
      setIsRunning(false);
    }
  }, []);

  return { outputs, isRunning, error, startRun, stopRun, reset };
}
