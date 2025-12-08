"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DollarSign, TrendingUp, Package, ShoppingCart, Star, Download, Eye } from "lucide-react";
import { toast } from "sonner";

interface SellerStats {
  total_sales: number;
  total_revenue: number;
  rating: number;
  active_listings: number;
}

interface Listing {
  id: number;
  title: string;
  category: string;
  price: number;
  downloads: number;
  rating: number;
  status: string;
}

interface Purchase {
  id: number;
  listing_id: number;
  amount: number;
  platform_fee: number;
  seller_amount: number;
  status: string;
  created_at: string;
}

export default function MySalesPage() {
  const [stats, setStats] = useState<SellerStats | null>(null);
  const [listings, setListings] = useState<Listing[]>([]);
  const [purchases, setPurchases] = useState<Purchase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, listingsRes, purchasesRes] = await Promise.all([
        fetch("http://localhost:8000/api/v1/marketplace/seller-stats"),
        fetch("http://localhost:8000/api/v1/marketplace/my-listings"),
        fetch("http://localhost:8000/api/v1/marketplace/my-purchases")
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      if (listingsRes.ok) {
        const listingsData = await listingsRes.json();
        setListings(listingsData.listings || []);
      }

      if (purchasesRes.ok) {
        const purchasesData = await purchasesRes.json();
        setPurchases(purchasesData.purchases || []);
      }
    } catch (error) {
      console.error("Failed to fetch data:", error);
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-green-600 to-blue-600 bg-clip-text text-transparent">
          My Sales Dashboard
        </h1>
        <p className="text-muted-foreground">
          Track your earnings and manage your marketplace listings
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              Total Revenue
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              ${stats?.total_revenue.toFixed(2) || "0.00"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              After 15% platform fee
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <ShoppingCart className="h-4 w-4" />
              Total Sales
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {stats?.total_sales || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Completed transactions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Package className="h-4 w-4" />
              Active Listings
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {stats?.active_listings || 0}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Published items
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <Star className="h-4 w-4" />
              Seller Rating
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold flex items-center gap-2">
              {stats?.rating.toFixed(1) || "0.0"}
              <Star className="h-6 w-6 fill-yellow-400 text-yellow-400" />
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Average rating
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="listings" className="space-y-4">
        <TabsList>
          <TabsTrigger value="listings">My Listings</TabsTrigger>
          <TabsTrigger value="sales">Recent Sales</TabsTrigger>
          <TabsTrigger value="purchases">My Purchases</TabsTrigger>
        </TabsList>

        {/* My Listings Tab */}
        <TabsContent value="listings" className="space-y-4">
          {listings.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center h-64 space-y-4">
                <Package className="h-16 w-16 text-muted-foreground" />
                <div className="text-center space-y-2">
                  <h3 className="text-xl font-semibold">No listings yet</h3>
                  <p className="text-muted-foreground">
                    Create your first agent or app to start selling!
                  </p>
                </div>
                <Button>Create Listing</Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {listings.map((listing) => (
                <Card key={listing.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <Badge variant="secondary">{listing.category}</Badge>
                      <Badge variant={listing.status === "active" ? "default" : "outline"}>
                        {listing.status}
                      </Badge>
                    </div>
                    <CardTitle className="mt-2">{listing.title}</CardTitle>
                    <CardDescription>
                      ${listing.price.toFixed(2)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Download className="h-3 w-3" />
                        <span>{listing.downloads} downloads</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                        <span>{listing.rating.toFixed(1)}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" className="flex-1">
                        <Eye className="h-3 w-3 mr-1" />
                        View
                      </Button>
                      <Button variant="outline" size="sm" className="flex-1">
                        Edit
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Recent Sales Tab */}
        <TabsContent value="sales" className="space-y-4">
          {purchases.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center h-64">
                <TrendingUp className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold">No sales yet</h3>
                <p className="text-muted-foreground">
                  Your sales will appear here once you make your first sale
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Recent Sales</CardTitle>
                <CardDescription>Your latest transactions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {purchases.map((purchase) => (
                    <div key={purchase.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">Order #{purchase.id}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(purchase.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-green-600">
                          +${purchase.seller_amount.toFixed(2)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          ${purchase.platform_fee.toFixed(2)} platform fee
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* My Purchases Tab */}
        <TabsContent value="purchases" className="space-y-4">
          {purchases.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center h-64">
                <ShoppingCart className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold">No purchases yet</h3>
                <p className="text-muted-foreground">
                  Browse the marketplace to find agents and apps to purchase
                </p>
                <Button className="mt-4">Browse Marketplace</Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>My Purchases</CardTitle>
                <CardDescription>Items you've bought</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {purchases.map((purchase) => (
                    <div key={purchase.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <p className="font-medium">Purchase #{purchase.id}</p>
                        <p className="text-sm text-muted-foreground">
                          {new Date(purchase.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">
                          ${purchase.amount.toFixed(2)}
                        </p>
                        <Badge variant="outline" className="mt-1">
                          {purchase.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
