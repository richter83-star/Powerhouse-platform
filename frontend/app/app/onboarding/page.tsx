"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, ArrowRight, ArrowLeft, Sparkles, Zap, Shield, BarChart3 } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

const STEPS = [
  {
    id: "welcome",
    title: "Welcome to Powerhouse",
    description: "Let's get you started with your AI-powered automation platform",
    icon: Sparkles
  },
  {
    id: "use-case",
    title: "What's your use case?",
    description: "Help us customize your experience",
    icon: Zap
  },
  {
    id: "tour",
    title: "Take a quick tour",
    description: "Learn about key features",
    icon: BarChart3
  },
  {
    id: "complete",
    title: "You're all set!",
    description: "Start building your first workflow",
    icon: CheckCircle2
  }
];

const USE_CASES = [
  {
    id: "compliance",
    name: "Compliance & Legal",
    description: "Regulatory compliance, legal research, document analysis"
  },
  {
    id: "sales",
    name: "Sales & Marketing",
    description: "Lead generation, customer research, market analysis"
  },
  {
    id: "operations",
    name: "Operations",
    description: "Process automation, workflow optimization, task management"
  },
  {
    id: "research",
    name: "Research & Analysis",
    description: "Data analysis, market research, competitive intelligence"
  },
  {
    id: "support",
    name: "Customer Support",
    description: "Ticket management, knowledge base, customer service"
  },
  {
    id: "other",
    name: "Other",
    description: "Custom use case or exploring the platform"
  }
];

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedUseCase, setSelectedUseCase] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  const handleNext = async () => {
    if (currentStep === STEPS.length - 1) {
      // Complete onboarding
      try {
        const response = await fetch("/api/onboarding/complete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ use_case: selectedUseCase })
        });

        if (response.ok) {
          toast.success("Onboarding completed!");
          router.push("/dashboard");
        } else {
          // Still redirect even if API call fails
          router.push("/dashboard");
        }
      } catch (error) {
        // Still redirect on error
        router.push("/dashboard");
      }
    } else {
      setCompletedSteps(new Set([...completedSteps, currentStep]));
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    router.push("/dashboard");
  };

  const progress = ((currentStep + 1) / STEPS.length) * 100;
  const step = STEPS[currentStep];
  const Icon = step.icon;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Icon className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle>{step.title}</CardTitle>
                <CardDescription>{step.description}</CardDescription>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={handleSkip}>
              Skip
            </Button>
          </div>
          <Progress value={progress} className="h-2" />
          <p className="text-sm text-muted-foreground mt-2">
            Step {currentStep + 1} of {STEPS.length}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {step.id === "welcome" && (
            <div className="space-y-4">
              <div className="text-center py-8">
                <Sparkles className="h-16 w-16 text-primary mx-auto mb-4" />
                <h3 className="text-2xl font-bold mb-2">Welcome to Powerhouse!</h3>
                <p className="text-muted-foreground">
                  Your AI-powered automation platform is ready. Let's set it up in just a few steps.
                </p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4">
                  <Zap className="h-8 w-8 text-primary mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Powerful Agents</h4>
                  <p className="text-sm text-muted-foreground">19+ specialized AI agents</p>
                </div>
                <div className="text-center p-4">
                  <Shield className="h-8 w-8 text-primary mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Enterprise Ready</h4>
                  <p className="text-sm text-muted-foreground">Secure and scalable</p>
                </div>
                <div className="text-center p-4">
                  <BarChart3 className="h-8 w-8 text-primary mx-auto mb-2" />
                  <h4 className="font-semibold mb-1">Analytics</h4>
                  <p className="text-sm text-muted-foreground">Track and optimize</p>
                </div>
              </div>
            </div>
          )}

          {step.id === "use-case" && (
            <div className="space-y-4">
              <p className="text-center text-muted-foreground mb-6">
                Select your primary use case to get personalized recommendations
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {USE_CASES.map((useCase) => (
                  <button
                    key={useCase.id}
                    onClick={() => setSelectedUseCase(useCase.id)}
                    className={`p-4 border-2 rounded-lg text-left transition-all ${
                      selectedUseCase === useCase.id
                        ? "border-primary bg-primary/5"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <h4 className="font-semibold mb-1">{useCase.name}</h4>
                    <p className="text-sm text-muted-foreground">{useCase.description}</p>
                  </button>
                ))}
              </div>
            </div>
          )}

          {step.id === "tour" && (
            <div className="space-y-4">
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-2">Dashboard</h4>
                  <p className="text-sm text-muted-foreground">
                    Your central command center for monitoring agents, workflows, and performance metrics.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-2">Agent Builder</h4>
                  <p className="text-sm text-muted-foreground">
                    Create and customize AI agents tailored to your specific needs.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-2">Workflows</h4>
                  <p className="text-sm text-muted-foreground">
                    Orchestrate multiple agents to automate complex business processes.
                  </p>
                </div>
                <div className="p-4 border rounded-lg">
                  <h4 className="font-semibold mb-2">Analytics</h4>
                  <p className="text-sm text-muted-foreground">
                    Track performance, usage, and optimize your automation strategies.
                  </p>
                </div>
              </div>
            </div>
          )}

          {step.id === "complete" && (
            <div className="text-center py-8 space-y-4">
              <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
              <h3 className="text-2xl font-bold">You're all set!</h3>
              <p className="text-muted-foreground">
                Your Powerhouse platform is ready. Start by creating your first workflow or exploring the dashboard.
              </p>
            </div>
          )}

          <div className="flex justify-between pt-4">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={currentStep === 0}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <Button
              onClick={handleNext}
              disabled={step.id === "use-case" && !selectedUseCase}
            >
              {currentStep === STEPS.length - 1 ? "Get Started" : "Next"}
              {currentStep < STEPS.length - 1 && <ArrowRight className="h-4 w-4 ml-2" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

