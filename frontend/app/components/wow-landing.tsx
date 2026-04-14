
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Brain,
  GitBranch,
  Activity,
  Plug,
  Package,
  ShoppingBag,
  Database,
  Shield,
  Zap,
  ArrowRight,
  Terminal,
  ChevronRight,
  Network,
  Cpu,
  BarChart3,
  RefreshCw,
  Lock,
  CheckCircle,
} from 'lucide-react';

const CODE_EXAMPLE = `import { PowerhouseClient } from '@powerhouse/sdk';

const client = new PowerhouseClient({
  apiUrl: process.env.POWERHOUSE_API_URL,
  apiKey: process.env.POWERHOUSE_API_KEY,
});

// Orchestrate 3 agents with consensus voting
const result = await client.orchestrate({
  agents: ['react', 'debate', 'evaluator'],
  task: 'Analyze Q3 revenue patterns and forecast Q4',
  mode: 'consensus',
  options: { maxTokens: 4096, temperature: 0.2 },
});

console.log(result.consensus);   // final answer
console.log(result.confidence);  // 0.94
console.log(result.reasoning);   // chain-of-thought`;

const REST_EXAMPLE = `POST /api/v1/orchestrate
Authorization: Bearer <api_key>

{
  "agents": ["react", "debate", "evaluator"],
  "task": "Analyze Q3 revenue patterns",
  "mode": "consensus"
}

// 200 OK
{
  "consensus": "Revenue grew 18% YoY driven by...",
  "confidence": 0.94,
  "agents_used": 3,
  "latency_ms": 1842
}`;

const systems = [
  {
    icon: Brain,
    name: 'AI Agent Orchestration',
    description: '19 specialized agents — reasoning, memory, debate, reflection, and autonomous loops.',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Network,
    name: 'Multi-Agent Coordination',
    description: 'Swarm, hierarchical, and consensus voting. Route tasks to the optimal agent config.',
    color: 'from-violet-500 to-purple-500',
  },
  {
    icon: Activity,
    name: 'Real-Time Observability',
    description: 'Circuit breakers, telemetry, checkpoints, and health dashboards out of the box.',
    color: 'from-emerald-500 to-green-500',
  },
  {
    icon: GitBranch,
    name: 'CI/CD Pipelines',
    description: 'Automated test and deploy flows. Rollback, canary, and blue-green deployments.',
    color: 'from-orange-500 to-amber-500',
  },
  {
    icon: Plug,
    name: 'Integrations & Webhooks',
    description: 'Connect your stack. REST webhooks, data pipelines, and 40+ connectors.',
    color: 'from-pink-500 to-rose-500',
  },
  {
    icon: Package,
    name: 'Plugin Architecture',
    description: 'Ship custom capabilities as plugins. Hot-reload without restarts.',
    color: 'from-teal-500 to-cyan-500',
  },
  {
    icon: RefreshCw,
    name: 'Continuous Learning',
    description: 'Curriculum adaptation, meta-evolution, and exponential self-improvement loops.',
    color: 'from-indigo-500 to-blue-500',
  },
  {
    icon: Shield,
    name: 'Enterprise Security',
    description: 'JWT auth, RBAC, multi-tenant isolation, audit logging, and compliance checks.',
    color: 'from-red-500 to-rose-500',
  },
];

const capabilities = [
  '19 AI Agents',
  'REST + SDK',
  'Real-Time Telemetry',
  'Plugin System',
  'CI/CD Built-in',
  'Multi-Tenant',
  'RBAC',
  'Auto-Retrain',
  'Webhook Events',
  'Self-Updating',
];

function TerminalWindow({ code, title }: { code: string; title: string }) {
  const [typed, setTyped] = useState('');

  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      if (i <= code.length) {
        setTyped(code.slice(0, i));
        i++;
      } else {
        clearInterval(interval);
      }
    }, 18);
    return () => clearInterval(interval);
  }, [code]);

  return (
    <div className="rounded-xl border border-white/10 overflow-hidden shadow-2xl shadow-black/50">
      {/* Title bar */}
      <div className="bg-slate-900 border-b border-white/10 px-4 py-3 flex items-center gap-3">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/70" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
          <div className="w-3 h-3 rounded-full bg-green-500/70" />
        </div>
        <span className="text-xs text-slate-400 font-mono">{title}</span>
      </div>
      {/* Code body */}
      <div className="bg-slate-950 p-5 overflow-x-auto">
        <pre className="text-xs sm:text-sm font-mono text-slate-300 leading-relaxed whitespace-pre-wrap">
          {typed}
          <span className="inline-block w-2 h-4 bg-blue-400 animate-pulse ml-0.5 align-middle" />
        </pre>
      </div>
    </div>
  );
}

function StaticCodeBlock({ code, title }: { code: string; title: string }) {
  return (
    <div className="rounded-xl border border-white/10 overflow-hidden shadow-2xl shadow-black/50">
      <div className="bg-slate-900 border-b border-white/10 px-4 py-3 flex items-center gap-3">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/70" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
          <div className="w-3 h-3 rounded-full bg-green-500/70" />
        </div>
        <span className="text-xs text-slate-400 font-mono">{title}</span>
      </div>
      <div className="bg-slate-950 p-5 overflow-x-auto">
        <pre className="text-xs sm:text-sm font-mono text-slate-300 leading-relaxed whitespace-pre">
          {code}
        </pre>
      </div>
    </div>
  );
}

export function WowLanding() {
  const [mounted, setMounted] = useState(false);
  const [capIdx, setCapIdx] = useState(0);

  useEffect(() => {
    setMounted(true);
    const t = setInterval(() => setCapIdx((i) => (i + 1) % capabilities.length), 1800);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* Fixed background glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 left-1/3 w-[600px] h-[600px] bg-blue-600/10 rounded-full blur-[120px]" />
        <div className="absolute top-1/2 -right-40 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-cyan-600/8 rounded-full blur-[100px]" />
      </div>

      <div className="relative">
        {/* ─── HERO ─────────────────────────────────────────────── */}
        <section className="min-h-screen flex flex-col justify-center px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto pt-24 pb-20">
          <div
            className={`transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'}`}
          >
            {/* Capabilities ticker */}
            <div className="flex items-center gap-3 mb-8">
              <Badge className="bg-blue-500/15 text-blue-300 border-blue-500/30 text-xs px-3 py-1">
                Enterprise AI Infrastructure
              </Badge>
              <div className="flex items-center gap-2 text-sm text-slate-400">
                <Terminal className="w-3.5 h-3.5" />
                <span className="font-mono text-blue-400 min-w-[140px] transition-all duration-300">
                  {capabilities[capIdx]}
                </span>
              </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
              {/* Left: headline */}
              <div>
                <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.05] mb-6">
                  <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                    The platform
                  </span>
                  <br />
                  <span className="bg-gradient-to-r from-blue-400 via-violet-400 to-cyan-400 bg-clip-text text-transparent">
                    serious developers
                  </span>
                  <br />
                  <span className="bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                    build on.
                  </span>
                </h1>

                <p className="text-lg sm:text-xl text-slate-400 mb-8 leading-relaxed max-w-xl">
                  Orchestrate 19+ AI agents via REST or SDK. Full observability, CI/CD,
                  plugin architecture, and enterprise security — production-ready from day one.
                </p>

                <div className="flex flex-wrap gap-3 mb-10">
                  <Link href="/signup">
                    <Button
                      size="lg"
                      className="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white font-semibold px-6 shadow-lg shadow-blue-500/25 transition-all duration-200"
                    >
                      Start Building
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                  <Link href="http://localhost:8001/docs" target="_blank">
                    <Button
                      size="lg"
                      variant="outline"
                      className="border-white/20 text-slate-200 hover:bg-white/10 hover:border-white/30 font-semibold px-6"
                    >
                      <Terminal className="w-4 h-4 mr-2" />
                      API Docs
                    </Button>
                  </Link>
                </div>

                {/* Trust signals */}
                <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                  {[
                    'JWT + RBAC auth',
                    'Multi-tenant isolation',
                    'OpenAPI docs included',
                    'Docker-ready',
                  ].map((s) => (
                    <div key={s} className="flex items-center gap-1.5">
                      <CheckCircle className="w-3.5 h-3.5 text-green-500" />
                      {s}
                    </div>
                  ))}
                </div>
              </div>

              {/* Right: animated terminal */}
              <div
                className={`transition-all duration-700 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
              >
                <TerminalWindow code={CODE_EXAMPLE} title="orchestrate.ts" />
              </div>
            </div>
          </div>
        </section>

        {/* ─── SYSTEMS GRID ────────────────────────────────────── */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto py-20 border-t border-white/5">
          <div className="text-center mb-12">
            <Badge className="bg-violet-500/15 text-violet-300 border-violet-500/30 mb-4">
              Full-Stack AI Platform
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Every system you need, connected
            </h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Not just an LLM wrapper. A complete operating environment for AI-powered applications.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {systems.map((sys) => {
              const Icon = sys.icon;
              return (
                <div
                  key={sys.name}
                  className="group p-5 rounded-xl bg-white/3 border border-white/8 hover:bg-white/6 hover:border-white/15 transition-all duration-300 cursor-default"
                >
                  <div
                    className={`inline-flex p-2.5 rounded-lg bg-gradient-to-br ${sys.color} bg-opacity-10 mb-4`}
                    style={{ background: 'rgba(255,255,255,0.06)' }}
                  >
                    <Icon className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="font-semibold text-white text-sm mb-1.5">{sys.name}</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">{sys.description}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ─── API / REST SECTION ──────────────────────────────── */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto py-20 border-t border-white/5">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
            <div>
              <Badge className="bg-emerald-500/15 text-emerald-300 border-emerald-500/30 mb-6">
                REST API + SDK
              </Badge>
              <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
                Integrate in minutes,
                <br />
                <span className="text-emerald-400">not months</span>
              </h2>
              <p className="text-slate-400 mb-8 leading-relaxed">
                Full OpenAPI documentation, language-agnostic REST endpoints, and an official
                TypeScript SDK. Auth via API keys or JWT. Every response includes structured
                reasoning traces, confidence scores, and agent attribution.
              </p>
              <ul className="space-y-3">
                {[
                  'OpenAPI 3.1 schema — import into any client',
                  'Streaming responses via SSE',
                  'Webhook events for async workflows',
                  'Rate limiting and usage analytics built-in',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-slate-300">
                    <ChevronRight className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <StaticCodeBlock code={REST_EXAMPLE} title="POST /api/v1/orchestrate" />
          </div>
        </section>

        {/* ─── FEATURES GRID ───────────────────────────────────── */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto py-20 border-t border-white/5">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Built for the way developers actually work
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Cpu,
                title: '19 Specialized Agents',
                body: 'ReAct, debate, tree-of-thought, chain-of-thought, swarm consensus, adaptive memory, meta-evolver — each optimized for different problem classes.',
                color: 'text-blue-400',
              },
              {
                icon: Zap,
                title: 'Self-Updating Models',
                body: 'Exponential learning loops, curriculum adaptation, and meta-evolution. The system improves itself based on observed performance, no manual retraining required.',
                color: 'text-yellow-400',
              },
              {
                icon: BarChart3,
                title: 'Real-Time Observability',
                body: 'Counters, gauges, histograms, and circuit breakers. Every agent execution is traced. Every failure is checkpointed. Full audit log for compliance.',
                color: 'text-emerald-400',
              },
              {
                icon: GitBranch,
                title: 'CI/CD Integration',
                body: 'Automated pipelines for model updates and application deploys. Canary releases, blue-green deployments, and instant rollback — all from the dashboard.',
                color: 'text-violet-400',
              },
              {
                icon: Lock,
                title: 'Enterprise Security',
                body: 'JWT authentication, role-based access control, multi-tenant data isolation, and rate limiting. SOC-2-ready audit logging on every action.',
                color: 'text-red-400',
              },
              {
                icon: Package,
                title: 'Plugin Architecture',
                body: 'Extend without forking. Drop in custom agent plugins, data connectors, or workflow steps. Hot-reload in development, zero-downtime in production.',
                color: 'text-pink-400',
              },
            ].map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.title}
                  className="p-6 rounded-xl bg-white/3 border border-white/8 hover:bg-white/5 hover:border-white/12 transition-all duration-300"
                >
                  <Icon className={`w-6 h-6 ${f.color} mb-4`} />
                  <h3 className="font-semibold text-white mb-2">{f.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{f.body}</p>
                </div>
              );
            })}
          </div>
        </section>

        {/* ─── CTA ─────────────────────────────────────────────── */}
        <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto py-24 border-t border-white/5">
          <div className="text-center max-w-2xl mx-auto">
            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
              Ready to ship?
            </h2>
            <p className="text-slate-400 mb-10 text-lg leading-relaxed">
              Docker Compose up in 5 minutes. Connect your first agent in 10.
              Full enterprise deployment guide included.
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Link href="/signup">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white font-semibold px-8 py-3 text-base shadow-lg shadow-blue-500/25"
                >
                  Create Account
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </Link>
              <Link href="/login">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white/20 text-slate-200 hover:bg-white/10 hover:border-white/30 font-semibold px-8 py-3 text-base"
                >
                  Sign In
                </Button>
              </Link>
            </div>

            <p className="text-xs text-slate-600 mt-8">
              Self-hosted · Docker · MIT License
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
