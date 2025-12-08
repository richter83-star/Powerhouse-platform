
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Network,
  Brain,
  Zap,
  TrendingUp,
  Shield,
  GitBranch,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Users,
  Cpu,
  Activity,
  BarChart3,
  Lightbulb,
  Rocket,
  Target,
  Globe,
  Lock,
  RefreshCw,
  MessageSquare,
  Database
} from 'lucide-react';

export function WowLanding() {
  const [mounted, setMounted] = useState(false);
  const [activeMetric, setActiveMetric] = useState(0);

  useEffect(() => {
    setMounted(true);
    const interval = setInterval(() => {
      setActiveMetric((prev) => (prev + 1) % 4);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const metrics = [
    { value: '19', label: 'AI Agents', icon: Brain, color: 'from-blue-500 to-cyan-500' },
    { value: '99.9%', label: 'Uptime', icon: Activity, color: 'from-green-500 to-emerald-500' },
    { value: '10x', label: 'Faster', icon: Zap, color: 'from-yellow-500 to-orange-500' },
    { value: '100%', label: 'Autonomous', icon: Cpu, color: 'from-purple-500 to-pink-500' },
  ];

  const features = [
    {
      icon: Brain,
      title: '19 Specialized AI Agents',
      description: 'Advanced reasoning, memory, debate, reflection, and autonomous agents working in perfect harmony',
      color: 'blue',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Network,
      title: 'Multi-Agent Orchestration',
      description: 'Intelligent coordination system that routes tasks to the optimal agent configuration',
      color: 'purple',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      icon: Lightbulb,
      title: 'Continuous Learning',
      description: 'Self-improving system with real-time model updates, performance monitoring, and adaptive optimization',
      color: 'green',
      gradient: 'from-green-500 to-emerald-500',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Built-in governance, compliance checks, content filtering, and security protocols',
      color: 'red',
      gradient: 'from-red-500 to-rose-500',
    },
    {
      icon: Rocket,
      title: 'Plugin Architecture',
      description: 'Extensible system with custom plugins, integrations, and deployment pipelines',
      color: 'indigo',
      gradient: 'from-indigo-500 to-blue-500',
    },
    {
      icon: BarChart3,
      title: 'Real-Time Analytics',
      description: 'Comprehensive monitoring, performance tracking, and business intelligence dashboards',
      color: 'orange',
      gradient: 'from-orange-500 to-amber-500',
    },
  ];

  const agentCategories = [
    { name: 'Reasoning', count: 4, icon: Brain, color: 'blue' },
    { name: 'Memory', count: 4, icon: Database, color: 'green' },
    { name: 'Coordination', count: 4, icon: Network, color: 'purple' },
    { name: 'Analysis', count: 4, icon: BarChart3, color: 'orange' },
    { name: 'Autonomous', count: 3, icon: Cpu, color: 'pink' },
  ];

  const capabilities = [
    'Multi-Perspective Analysis',
    'Self-Healing Systems',
    'Real-Time Adaptation',
    'Policy Enforcement',
    'Autonomous Retraining',
    'Dynamic Configuration',
    'Proactive Goal Setting',
    'Advanced Planning',
    'Context Memory',
    'Tool Integration',
    'Swarm Intelligence',
    'Hierarchical Delegation',
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      {/* Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 via-purple-600/10 to-pink-600/10 animate-gradient-xy" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-2000" />
      </div>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          {/* Badge */}
          <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-xl border border-white/20 mb-8 transition-all duration-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}`}>
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <span className="text-sm font-medium">Powered by 19 Advanced AI Agents</span>
          </div>

          {/* Main Heading */}
          <h1 className={`text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent transition-all duration-700 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
            The Future of
            <br />
            Intelligent Automation
          </h1>

          {/* Subheading */}
          <p className={`text-xl sm:text-2xl text-slate-300 mb-8 max-w-3xl mx-auto transition-all duration-700 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
            Enterprise-grade multi-agent platform that learns, adapts, and scales autonomously to solve any business challenge
          </p>

          {/* CTA Buttons */}
          <div className={`flex flex-col sm:flex-row gap-4 justify-center mb-16 transition-all duration-700 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
            <Link href="/signup">
              <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-xl shadow-2xl shadow-blue-500/50 transition-all duration-300 hover:scale-105">
                Get Started Free
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="border-white/20 bg-white/5 backdrop-blur-xl hover:bg-white/10 text-white px-8 py-6 text-lg rounded-xl transition-all duration-300 hover:scale-105">
                View Demo
                <Rocket className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>

          {/* Animated Metrics */}
          <div className={`grid grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto transition-all duration-700 delay-400 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
            {metrics.map((metric, index) => {
              const Icon = metric.icon;
              return (
                <Card
                  key={index}
                  className={`bg-white/5 backdrop-blur-xl border-white/10 transition-all duration-500 hover:scale-110 hover:bg-white/10 ${
                    activeMetric === index ? 'ring-2 ring-white/30 scale-105' : ''
                  }`}
                >
                  <CardContent className="p-6">
                    <Icon className={`w-8 h-8 mb-3 mx-auto bg-gradient-to-r ${metric.color} bg-clip-text text-transparent`} />
                    <p className="text-3xl font-bold mb-1 text-white">{metric.value}</p>
                    <p className="text-sm text-slate-400">{metric.label}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Agent Network Visualization */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-blue-500/20 text-blue-300 border-blue-500/30">19 AI Agents</Badge>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Multi-Agent Intelligence Network
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Each agent specializes in unique capabilities, working together as a unified intelligence
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6 mb-12">
            {agentCategories.map((category, index) => {
              const Icon = category.icon;
              const colors = {
                blue: 'from-blue-500 to-cyan-500',
                green: 'from-green-500 to-emerald-500',
                purple: 'from-purple-500 to-pink-500',
                orange: 'from-orange-500 to-amber-500',
                pink: 'from-pink-500 to-rose-500',
              };
              
              return (
                <Card
                  key={index}
                  className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group cursor-pointer"
                >
                  <CardContent className="p-6 text-center">
                    <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br ${colors[category.color as keyof typeof colors]} p-0.5 group-hover:scale-110 transition-transform duration-300`}>
                      <div className="w-full h-full bg-slate-950 rounded-2xl flex items-center justify-center">
                        <Icon className="w-8 h-8 text-white" />
                      </div>
                    </div>
                    <p className="font-semibold text-lg mb-1 text-white">{category.name}</p>
                    <p className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                      {category.count}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Capabilities Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {capabilities.map((capability, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-4 py-3 rounded-lg bg-white/5 backdrop-blur-xl border border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105"
              >
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <span className="text-sm text-slate-300">{capability}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-purple-500/20 text-purple-300 border-purple-500/30">Platform Features</Badge>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              Built for Enterprise Scale
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Production-ready platform with enterprise security, continuous learning, and autonomous operations
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card
                  key={index}
                  className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group cursor-pointer overflow-hidden"
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
                  <CardContent className="p-8 relative">
                    <div className={`w-14 h-14 mb-6 rounded-xl bg-gradient-to-br ${feature.gradient} p-0.5 group-hover:scale-110 transition-transform duration-300`}>
                      <div className="w-full h-full bg-slate-950 rounded-xl flex items-center justify-center">
                        <Icon className="w-7 h-7 text-white" />
                      </div>
                    </div>
                    <h3 className="text-xl font-bold mb-3 text-white">{feature.title}</h3>
                    <p className="text-slate-400 leading-relaxed">{feature.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-green-500/20 text-green-300 border-green-500/30">Industry Applications</Badge>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-green-400 to-emerald-400 bg-clip-text text-transparent">
              Powering Every Industry
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              From compliance to customer support, our agents adapt to any business challenge
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: Shield, title: 'Compliance & Risk', desc: 'Automated compliance monitoring' },
              { icon: MessageSquare, title: 'Customer Support', desc: 'Intelligent support automation' },
              { icon: TrendingUp, title: 'Sales & Marketing', desc: 'Predictive analytics & insights' },
              { icon: Target, title: 'Operations', desc: 'Process optimization' },
              { icon: Brain, title: 'Research & Development', desc: 'Accelerated innovation' },
              { icon: Globe, title: 'Supply Chain', desc: 'Smart logistics management' },
              { icon: Users, title: 'Human Resources', desc: 'Talent optimization' },
              { icon: BarChart3, title: 'Finance', desc: 'Intelligent forecasting' },
            ].map((useCase, index) => {
              const Icon = useCase.icon;
              return (
                <Card
                  key={index}
                  className="bg-white/5 backdrop-blur-xl border-white/10 hover:border-white/30 transition-all duration-300 hover:scale-105 group cursor-pointer"
                >
                  <CardContent className="p-6 text-center">
                    <Icon className="w-10 h-10 mx-auto mb-4 text-green-400 group-hover:scale-110 transition-transform duration-300" />
                    <h3 className="font-semibold text-lg mb-2 text-white">{useCase.title}</h3>
                    <p className="text-sm text-slate-400">{useCase.desc}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-5xl mx-auto">
          <Card className="bg-slate-900/80 backdrop-blur-xl border-white/20 overflow-hidden relative">
            {/* Darker gradient overlay for better contrast */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-600/30 via-purple-600/30 to-pink-600/30 animate-gradient-x" />
            {/* Dark overlay to ensure text visibility */}
            <div className="absolute inset-0 bg-slate-950/40" />
            <CardContent className="p-12 relative z-10">
              <div className="grid md:grid-cols-3 gap-12 text-center">
                <div>
                  <p className="text-5xl font-bold mb-2 text-white drop-shadow-[0_0_20px_rgba(255,255,255,0.5)]">10x</p>
                  <p className="text-slate-200 font-medium">Faster Processing</p>
                </div>
                <div>
                  <p className="text-5xl font-bold mb-2 text-white drop-shadow-[0_0_20px_rgba(255,255,255,0.5)]">99.9%</p>
                  <p className="text-slate-200 font-medium">System Uptime</p>
                </div>
                <div>
                  <p className="text-5xl font-bold mb-2 text-white drop-shadow-[0_0_20px_rgba(255,255,255,0.5)]">100%</p>
                  <p className="text-slate-200 font-medium">Autonomous</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-24 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl sm:text-5xl font-bold mb-6 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Ready to Transform Your Business?
          </h2>
          <p className="text-xl text-slate-300 mb-8 max-w-2xl mx-auto">
            Join leading enterprises using AI agents to automate, optimize, and scale their operations
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-xl shadow-2xl shadow-blue-500/50 transition-all duration-300 hover:scale-105">
                Start Building Today
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline" className="border-white/20 bg-white/5 backdrop-blur-xl hover:bg-white/10 text-white px-8 py-6 text-lg rounded-xl transition-all duration-300 hover:scale-105">
                Explore Platform
                <Network className="ml-2 w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative py-12 px-4 sm:px-6 lg:px-8 border-t border-white/10">
        <div className="max-w-7xl mx-auto text-center text-slate-400">
          <p>© 2025 Powerhouse B2B Platform. Built with 19 AI Agents.</p>
          <p className="text-sm mt-2">Enterprise-grade • Self-learning • Autonomous</p>
        </div>
      </footer>
    </div>
  );
}

// Add custom animation keyframes to global CSS
const customStyles = `
@keyframes gradient-xy {
  0%, 100% {
    background-position: 0% 0%;
  }
  25% {
    background-position: 100% 0%;
  }
  50% {
    background-position: 100% 100%;
  }
  75% {
    background-position: 0% 100%;
  }
}

@keyframes gradient-x {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.animate-gradient-xy {
  background-size: 400% 400%;
  animation: gradient-xy 15s ease infinite;
}

.animate-gradient-x {
  background-size: 200% 200%;
  animation: gradient-x 3s ease infinite;
}

.delay-1000 {
  animation-delay: 1s;
}

.delay-2000 {
  animation-delay: 2s;
}
`;
