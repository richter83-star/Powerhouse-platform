
"""
Marketplace API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

router = APIRouter()

# Pydantic models
class ListingCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    title: str
    description: str
    category: str
    item_type: str
    price: float
    complexity_score: Optional[int] = 1
    preview_images: Optional[List[str]] = []
    demo_url: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = {}

class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    seller_id: int
    seller_name: str
    title: str
    description: str
    category: str
    item_type: str
    price: float
    complexity_score: int
    preview_images: List[str]
    demo_url: Optional[str]
    downloads: int
    rating: float
    status: str
    created_at: datetime

class PurchaseRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    listing_id: int
    payment_method_id: str

class SellerStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    total_sales: int
    total_revenue: float
    rating: float
    active_listings: int

# Mock database (replace with real database in production)
mock_listings = []
mock_purchases = []
mock_sellers = {}

@router.get("/marketplace/listings")
async def get_listings(
    category: Optional[str] = None,
    item_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "recent"
):
    """Get marketplace listings with filters"""
    # In production, query database
    listings = mock_listings.copy()
    
    # Apply filters
    if category:
        listings = [l for l in listings if l["category"] == category]
    if item_type:
        listings = [l for l in listings if l["item_type"] == item_type]
    if min_price:
        listings = [l for l in listings if l["price"] >= min_price]
    if max_price:
        listings = [l for l in listings if l["price"] <= max_price]
    
    # Sort
    if sort_by == "price_low":
        listings.sort(key=lambda x: x["price"])
    elif sort_by == "price_high":
        listings.sort(key=lambda x: x["price"], reverse=True)
    elif sort_by == "popular":
        listings.sort(key=lambda x: x["downloads"], reverse=True)
    elif sort_by == "rating":
        listings.sort(key=lambda x: x["rating"], reverse=True)
    else:  # recent
        listings.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"listings": listings, "total": len(listings)}

@router.get("/marketplace/listings/{listing_id}")
async def get_listing(listing_id: int):
    """Get single listing details"""
    listing = next((l for l in mock_listings if l["id"] == listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing

@router.post("/marketplace/listings")
async def create_listing(listing: ListingCreate):
    """Create a new marketplace listing"""
    # In production, save to database
    new_listing = {
        "id": len(mock_listings) + 1,
        "seller_id": 1,  # Get from auth
        "seller_name": "Demo Seller",
        **listing.model_dump(),
        "downloads": 0,
        "rating": 0.0,
        "status": "active",
        "created_at": datetime.now().isoformat()
    }
    mock_listings.append(new_listing)
    return {"listing": new_listing, "message": "Listing created successfully"}

@router.post("/marketplace/purchase")
async def purchase_item(purchase: PurchaseRequest):
    """Purchase an item from marketplace"""
    listing = next((l for l in mock_listings if l["id"] == purchase.listing_id), None)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    # Calculate fees (15% platform commission)
    total_amount = listing["price"]
    platform_fee = total_amount * 0.15
    seller_amount = total_amount - platform_fee
    
    # In production:
    # 1. Process Stripe payment
    # 2. Save to database
    # 3. Transfer funds to seller
    # 4. Send notifications
    
    purchase_record = {
        "id": len(mock_purchases) + 1,
        "listing_id": purchase.listing_id,
        "buyer_id": 1,  # Get from auth
        "seller_id": listing["seller_id"],
        "amount": total_amount,
        "platform_fee": platform_fee,
        "seller_amount": seller_amount,
        "status": "completed",
        "created_at": datetime.now().isoformat()
    }
    mock_purchases.append(purchase_record)
    
    # Update listing downloads
    listing["downloads"] += 1
    
    return {
        "purchase": purchase_record,
        "message": "Purchase completed successfully"
    }

@router.get("/marketplace/my-listings")
async def get_my_listings():
    """Get current user's listings"""
    # In production, filter by authenticated user
    user_listings = [l for l in mock_listings if l["seller_id"] == 1]
    return {"listings": user_listings}

@router.get("/marketplace/my-purchases")
async def get_my_purchases():
    """Get current user's purchases"""
    # In production, filter by authenticated user
    user_purchases = [p for p in mock_purchases if p["buyer_id"] == 1]
    return {"purchases": user_purchases}

@router.get("/marketplace/seller-stats")
async def get_seller_stats():
    """Get seller statistics"""
    # In production, calculate from database
    user_purchases = [p for p in mock_purchases if p["seller_id"] == 1]
    user_listings = [l for l in mock_listings if l["seller_id"] == 1]
    
    total_revenue = sum(p["seller_amount"] for p in user_purchases)
    
    return {
        "total_sales": len(user_purchases),
        "total_revenue": total_revenue,
        "rating": 4.8,
        "active_listings": len([l for l in user_listings if l["status"] == "active"])
    }

@router.delete("/marketplace/listings/{listing_id}")
async def delete_listing(listing_id: int):
    """Delete a listing"""
    global mock_listings
    mock_listings = [l for l in mock_listings if l["id"] != listing_id]
    return {"message": "Listing deleted successfully"}
