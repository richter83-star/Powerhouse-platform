"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CreditCard, Download, Calendar, CheckCircle2, XCircle, AlertCircle, Plus, Trash2, Star, Activity } from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";

interface Subscription {
  id: string;
  status: "active" | "canceled" | "past_due" | "trialing";
  plan: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  amount: number;
  currency: string;
}

interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: "paid" | "open" | "void" | "uncollectible";
  date: string;
  period_start: string;
  period_end: string;
  pdf_url?: string;
}

interface PaymentMethod {
  id: string;
  type: "card";
  card: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
  };
  is_default: boolean;
}

interface UsageData {
  api_calls: number;
  agent_executions: number;
  workflow_runs: number;
  storage_gb: number;
  compute_hours: number;
  total_cost: number;
  limits?: {
    api_calls_per_hour?: number;
  };
}

function UsageDashboard() {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsage();
  }, []);

  const fetchUsage = async () => {
    try {
      const response = await fetch("/api/billing/usage/current-month");
      if (response.ok) {
        const data = await response.json();
        setUsage(data);
      }
    } catch (error) {
      console.error("Failed to fetch usage:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8 text-muted-foreground">Loading usage data...</div>;
  }

  if (!usage) {
    return <div className="text-center py-8 text-muted-foreground">No usage data available</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">API Calls</div>
          <div className="text-2xl font-bold mt-1">{usage.api_calls.toLocaleString()}</div>
          {usage.limits?.api_calls_per_hour && (
            <div className="text-xs text-muted-foreground mt-1">
              Limit: {usage.limits.api_calls_per_hour.toLocaleString()}/hour
            </div>
          )}
        </div>
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">Agent Executions</div>
          <div className="text-2xl font-bold mt-1">{usage.agent_executions.toLocaleString()}</div>
        </div>
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">Workflow Runs</div>
          <div className="text-2xl font-bold mt-1">{usage.workflow_runs.toLocaleString()}</div>
        </div>
        <div className="p-4 border rounded-lg">
          <div className="text-sm text-muted-foreground">Storage</div>
          <div className="text-2xl font-bold mt-1">{usage.storage_gb.toFixed(2)} GB</div>
        </div>
      </div>
      <div className="p-4 bg-primary/5 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-muted-foreground">Estimated Cost</div>
            <div className="text-2xl font-bold mt-1">
              ${usage.total_cost.toFixed(2)}
            </div>
            <div className="text-xs text-muted-foreground mt-1">This month</div>
          </div>
          <Activity className="h-8 w-8 text-primary" />
        </div>
      </div>
    </div>
  );
}

export default function BillingPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [showAddPaymentMethod, setShowAddPaymentMethod] = useState(false);
  const [setupIntentClientSecret, setSetupIntentClientSecret] = useState<string | null>(null);

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      setLoading(true);
      const [subRes, invRes, pmRes] = await Promise.all([
        fetch("/api/billing/subscription"),
        fetch("/api/billing/invoices"),
        fetch("/api/billing/payment-methods")
      ]);

      if (subRes.ok) {
        const subData = await subRes.json();
        setSubscription(subData);
      }

      if (invRes.ok) {
        const invData = await invRes.json();
        setInvoices(invData);
      }

      if (pmRes.ok) {
        const pmData = await pmRes.json();
        setPaymentMethods(pmData);
      }
    } catch (error) {
      toast.error("Failed to load billing information");
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (planId: string) => {
    try {
      setUpdating(true);
      const response = await fetch("/api/billing/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan_id: planId })
      });

      if (!response.ok) throw new Error("Failed to upgrade");

      const data = await response.json();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        toast.success("Subscription updated successfully");
        fetchBillingData();
      }
    } catch (error: any) {
      toast.error(error.message || "Failed to upgrade subscription");
    } finally {
      setUpdating(false);
    }
  };

  const handleCancel = async () => {
    if (!confirm("Are you sure you want to cancel your subscription? You'll continue to have access until the end of your billing period.")) {
      return;
    }

    try {
      setUpdating(true);
      const response = await fetch("/api/billing/subscription/cancel", {
        method: "POST"
      });

      if (!response.ok) throw new Error("Failed to cancel subscription");

      toast.success("Subscription will be canceled at the end of the billing period");
      fetchBillingData();
    } catch (error: any) {
      toast.error(error.message || "Failed to cancel subscription");
    } finally {
      setUpdating(false);
    }
  };

  const handleResume = async () => {
    try {
      setUpdating(true);
      const response = await fetch("/api/billing/subscription/resume", {
        method: "POST"
      });

      if (!response.ok) throw new Error("Failed to resume subscription");

      toast.success("Subscription resumed");
      fetchBillingData();
    } catch (error: any) {
      toast.error(error.message || "Failed to resume subscription");
    } finally {
      setUpdating(false);
    }
  };

  const formatCurrency = (amount: number, currency: string = "usd") => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase()
    }).format(amount / 100);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric"
    });
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      active: "default",
      trialing: "default",
      past_due: "destructive",
      canceled: "secondary"
    };

    return (
      <Badge variant={variants[status] || "outline"}>
        {status.replace("_", " ").toUpperCase()}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-muted-foreground">Loading billing information...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Billing & Subscription</h1>
        <p className="text-muted-foreground mt-2">Manage your subscription and billing information</p>
      </div>

      <Tabs defaultValue="subscription" className="space-y-6">
        <TabsList>
          <TabsTrigger value="subscription">Subscription</TabsTrigger>
          <TabsTrigger value="usage">Usage</TabsTrigger>
          <TabsTrigger value="invoices">Invoices</TabsTrigger>
          <TabsTrigger value="payment-methods">Payment Methods</TabsTrigger>
        </TabsList>

        <TabsContent value="subscription" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Current Subscription</CardTitle>
                  <CardDescription>Your active subscription plan</CardDescription>
                </div>
                {subscription && getStatusBadge(subscription.status)}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {subscription ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground">Plan</p>
                      <p className="text-lg font-semibold capitalize">{subscription.plan}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Amount</p>
                      <p className="text-lg font-semibold">
                        {formatCurrency(subscription.amount, subscription.currency)}
                        <span className="text-sm text-muted-foreground">/month</span>
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Current Period Start</p>
                      <p className="text-lg">{formatDate(subscription.current_period_start)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Current Period End</p>
                      <p className="text-lg">{formatDate(subscription.current_period_end)}</p>
                    </div>
                  </div>

                  {subscription.cancel_at_period_end && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                      <div className="flex items-start">
                        <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mr-2 mt-0.5" />
                        <div>
                          <p className="font-medium text-yellow-800 dark:text-yellow-200">
                            Subscription will be canceled
                          </p>
                          <p className="text-sm text-yellow-700 dark:text-yellow-300 mt-1">
                            Your subscription will end on {formatDate(subscription.current_period_end)}. You'll continue to have access until then.
                          </p>
                          <Button
                            variant="outline"
                            size="sm"
                            className="mt-2"
                            onClick={handleResume}
                            disabled={updating}
                          >
                            Resume Subscription
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-4">
                    <Link href="/settings/billing">
                      <Button variant="outline">
                        Change Plan
                      </Button>
                    </Link>
                    {!subscription.cancel_at_period_end && (
                      <Button
                        variant="destructive"
                        onClick={handleCancel}
                        disabled={updating}
                      >
                        Cancel Subscription
                      </Button>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">No active subscription</p>
                  <Link href="/settings/billing">
                    <Button>Choose a Plan</Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Month Usage</CardTitle>
              <CardDescription>Track your resource usage and limits</CardDescription>
            </CardHeader>
            <CardContent>
              <UsageDashboard />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invoices" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Invoice History</CardTitle>
              <CardDescription>View and download your invoices</CardDescription>
            </CardHeader>
            <CardContent>
              {invoices.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Date</TableHead>
                      <TableHead>Period</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell>{formatDate(invoice.date)}</TableCell>
                        <TableCell>
                          {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
                        </TableCell>
                        <TableCell>{formatCurrency(invoice.amount, invoice.currency)}</TableCell>
                        <TableCell>
                          {invoice.status === "paid" ? (
                            <Badge variant="default">
                              <CheckCircle2 className="h-3 w-3 mr-1" />
                              Paid
                            </Badge>
                          ) : invoice.status === "open" ? (
                            <Badge variant="outline">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Open
                            </Badge>
                          ) : (
                            <Badge variant="secondary">{invoice.status}</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {invoice.pdf_url && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => window.open(invoice.pdf_url, "_blank")}
                            >
                              <Download className="h-4 w-4 mr-2" />
                              Download
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No invoices yet
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payment-methods" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Payment Methods</CardTitle>
              <CardDescription>Manage your payment methods</CardDescription>
            </CardHeader>
            <CardContent>
              {paymentMethods.length > 0 ? (
                <div className="space-y-4">
                  {paymentMethods.map((pm) => (
                    <div
                      key={pm.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex items-center gap-4">
                        <CreditCard className="h-8 w-8 text-muted-foreground" />
                        <div>
                          <p className="font-medium">
                            {pm.card.brand.toUpperCase()} •••• {pm.card.last4}
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Expires {pm.card.exp_month}/{pm.card.exp_year}
                          </p>
                        </div>
                        {pm.is_default && (
                          <Badge variant="default">Default</Badge>
                        )}
                      </div>
                      <div className="flex gap-2">
                        {!pm.is_default && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={async () => {
                              try {
                                const response = await fetch(`/api/billing/payment-methods/${pm.id}/set-default`, {
                                  method: "POST"
                                });
                                if (response.ok) {
                                  toast.success("Default payment method updated");
                                  fetchBillingData();
                                }
                              } catch (error) {
                                toast.error("Failed to set default payment method");
                              }
                            }}
                          >
                            <Star className="h-4 w-4 mr-1" />
                            Set Default
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            if (!confirm("Are you sure you want to delete this payment method?")) return;
                            try {
                              const response = await fetch(`/api/billing/payment-methods/${pm.id}`, {
                                method: "DELETE"
                              });
                              if (response.ok) {
                                toast.success("Payment method deleted");
                                fetchBillingData();
                              }
                            } catch (error) {
                              toast.error("Failed to delete payment method");
                            }
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={async () => {
                      try {
                        const response = await fetch("/api/billing/payment-methods/setup-intent", {
                          method: "POST"
                        });
                        if (response.ok) {
                          const data = await response.json();
                          setSetupIntentClientSecret(data.client_secret);
                          setShowAddPaymentMethod(true);
                        }
                      } catch (error) {
                        toast.error("Failed to create setup intent");
                      }
                    }}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Payment Method
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground mb-4">No payment methods on file</p>
                  <Button
                    onClick={async () => {
                      try {
                        const response = await fetch("/api/billing/payment-methods/setup-intent", {
                          method: "POST"
                        });
                        if (response.ok) {
                          const data = await response.json();
                          setSetupIntentClientSecret(data.client_secret);
                          setShowAddPaymentMethod(true);
                        }
                      } catch (error) {
                        toast.error("Failed to create setup intent");
                      }
                    }}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Payment Method
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Payment Method Modal - Simplified version */}
      {showAddPaymentMethod && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg max-w-md w-full">
            <h3 className="text-lg font-semibold mb-4">Add Payment Method</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Payment method collection will be integrated with Stripe Elements.
              For now, use Stripe Checkout to add payment methods.
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setShowAddPaymentMethod(false);
                  setSetupIntentClientSecret(null);
                }}
              >
                Cancel
              </Button>
              <Button
                className="flex-1"
                onClick={() => {
                  // In production, integrate Stripe Elements here
                  toast.info("Stripe Elements integration needed for in-app payment method collection");
                  setShowAddPaymentMethod(false);
                }}
              >
                Continue
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

