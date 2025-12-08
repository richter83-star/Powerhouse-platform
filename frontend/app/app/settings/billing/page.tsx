"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Check } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";

interface Plan {
  id: string;
  name: string;
  price: number;
  currency: string;
  interval: "month" | "year";
  features: string[];
  trial_days?: number;
  annual_price?: number;
  annual_savings_percent?: number;
  popular?: boolean;
}

interface CurrentSubscription {
  plan_id: string;
  status: string;
}

export default function BillingSettingsPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [currentSubscription, setCurrentSubscription] = useState<CurrentSubscription | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [billingInterval, setBillingInterval] = useState<"month" | "year">("month");
  const [showChangePlanModal, setShowChangePlanModal] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [prorationPreview, setProrationPreview] = useState<any>(null);

  useEffect(() => {
    fetchPlans();
    fetchCurrentSubscription();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch("/api/billing/plans");
      if (!response.ok) throw new Error("Failed to fetch plans");
      const data = await response.json();
      setPlans(data);
    } catch (error) {
      toast.error("Failed to load plans");
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentSubscription = async () => {
    try {
      const response = await fetch("/api/billing/subscription");
      if (response.ok) {
        const data = await response.json();
        setCurrentSubscription({
          plan_id: data.plan_id || data.plan,
          status: data.status
        });
      }
    } catch (error) {
      // Ignore if no subscription
    }
  };

  const handleSubscribe = async (planId: string) => {
    try {
      setUpdating(planId);
      const response = await fetch("/api/billing/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          plan_id: planId,
          interval: billingInterval
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Failed to subscribe");
      }

      const data = await response.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        toast.success("Subscription updated successfully");
        fetchCurrentSubscription();
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to subscribe");
    } finally {
      setUpdating(null);
    }
  };

  const handleChangePlan = async (newPlanId: string) => {
    try {
      // Preview proration first
      const previewResponse = await fetch(
        `/api/billing/subscription/change-plan/preview?new_plan_id=${newPlanId}&interval=${billingInterval}`
      );
      if (previewResponse.ok) {
        const preview = await previewResponse.json();
        setProrationPreview(preview);
        setSelectedPlanId(newPlanId);
        setShowChangePlanModal(true);
      } else {
        // If preview fails, try to change plan directly
        await confirmChangePlan(newPlanId);
      }
    } catch (error: any) {
      toast.error("Failed to preview plan change");
    }
  };

  const confirmChangePlan = async (planId: string) => {
    try {
      setUpdating(planId);
      const response = await fetch("/api/billing/subscription/change-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          new_plan_id: planId,
          interval: billingInterval,
          proration_behavior: "always_invoice"
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "Failed to change plan");
      }

      toast.success("Plan changed successfully");
      setShowChangePlanModal(false);
      setProrationPreview(null);
      fetchCurrentSubscription();
    } catch (error: any) {
      toast.error(error.message || "Failed to change plan");
    } finally {
      setUpdating(null);
    }
  };

  const formatPrice = (price: number, currency: string = "usd") => {
    if (price === 0) return "Free";
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase()
    }).format(price / 100);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading plans...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Subscription Plans</h1>
        <p className="text-muted-foreground mt-2">Choose the plan that's right for you</p>
      </div>

      {/* Billing Interval Toggle */}
      <div className="mb-6 flex items-center justify-center gap-4">
        <span className={`text-sm font-medium ${billingInterval === "month" ? "text-primary" : "text-muted-foreground"}`}>
          Monthly
        </span>
        <button
          onClick={() => setBillingInterval(billingInterval === "month" ? "year" : "month")}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
            billingInterval === "year" ? "bg-primary" : "bg-gray-300"
          }`}
        >
          <span
            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              billingInterval === "year" ? "translate-x-6" : "translate-x-1"
            }`}
          />
        </button>
        <span className={`text-sm font-medium ${billingInterval === "year" ? "text-primary" : "text-muted-foreground"}`}>
          Annual
          {billingInterval === "year" && (
            <Badge variant="secondary" className="ml-2">Save up to 17%</Badge>
          )}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => {
          const isCurrent = currentSubscription?.plan_id === plan.id;
          const isActive = currentSubscription?.status === "active";

          return (
            <Card
              key={plan.id}
              className={`relative ${plan.popular ? "border-primary shadow-lg" : ""}`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-primary">Most Popular</Badge>
                </div>
              )}
              <CardHeader>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <div className="mt-4">
                  <span className="text-4xl font-bold">
                    {formatPrice(
                      billingInterval === "year" && plan.annual_price 
                        ? plan.annual_price 
                        : plan.price, 
                      plan.currency
                    )}
                  </span>
                  {plan.price > 0 && (
                    <span className="text-muted-foreground">
                      /{billingInterval === "month" ? "month" : "year"}
                    </span>
                  )}
                  {billingInterval === "year" && plan.annual_savings_percent && (
                    <div className="text-sm text-green-600 dark:text-green-400 mt-1">
                      Save {plan.annual_savings_percent}%
                    </div>
                  )}
                </div>
                {plan.trial_days && plan.trial_days > 0 && (
                  <Badge variant="secondary" className="mt-2">
                    {plan.trial_days} days free trial
                  </Badge>
                )}
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="h-5 w-5 text-primary mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
                {isCurrent && isActive ? (
                  <div className="space-y-2">
                    <Button variant="outline" className="w-full" disabled>
                      Current Plan
                    </Button>
                    {/* Show upgrade/downgrade options for other plans */}
                    {plans.some(p => p.id !== plan.id && p.price !== 0) && (
                      <div className="text-xs text-center text-muted-foreground">
                        Want to change? Select another plan below
                      </div>
                    )}
                  </div>
                ) : (
                  <Button
                    className="w-full"
                    onClick={() => {
                      if (isCurrent && currentSubscription?.status !== "active") {
                        handleSubscribe(plan.id);
                      } else if (currentSubscription?.status === "active" && !isCurrent) {
                        // Change plan instead of new subscription
                        handleChangePlan(plan.id);
                      } else {
                        handleSubscribe(plan.id);
                      }
                    }}
                    disabled={updating === plan.id}
                  >
                    {updating === plan.id
                      ? "Processing..."
                      : isCurrent
                      ? "Resume"
                      : currentSubscription?.status === "active"
                      ? (plan.price > (plans.find(p => p.id === currentSubscription.plan_id)?.price || 0) ? "Upgrade" : "Downgrade")
                      : plan.price === 0
                      ? "Get Started"
                      : "Subscribe"}
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="mt-8 text-center text-sm text-muted-foreground">
        <p>
          Need help choosing? <Link href="/support" className="text-primary hover:underline">Contact support</Link>
        </p>
      </div>

      {/* Plan Change Confirmation Modal */}
      {showChangePlanModal && prorationPreview && selectedPlanId && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Confirm Plan Change</h3>
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">Proration Preview</p>
                {prorationPreview.proration && (
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span>Current Amount:</span>
                      <span>${(prorationPreview.proration.current_amount / 100).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>New Amount:</span>
                      <span>${(prorationPreview.proration.new_amount / 100).toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between font-semibold">
                      <span>Proration:</span>
                      <span className={prorationPreview.proration.proration_amount >= 0 ? "text-green-600" : "text-red-600"}>
                        ${(prorationPreview.proration.proration_amount / 100).toFixed(2)}
                      </span>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setShowChangePlanModal(false);
                    setProrationPreview(null);
                    setSelectedPlanId(null);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => confirmChangePlan(selectedPlanId)}
                  disabled={updating === selectedPlanId}
                >
                  {updating === selectedPlanId ? "Processing..." : "Confirm Change"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

