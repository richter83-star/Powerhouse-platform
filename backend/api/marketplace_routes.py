
"""
Marketplace API Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import stripe
import os
import logging

from config.settings import settings
from api.auth import get_current_user
from api.models import User as APIUser
from database.session import get_db
from database.models import (
    Seller, MarketplaceListing, MarketplacePurchase, MarketplaceReview
)

logger = logging.getLogger(__name__)

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


def _require_user_id(current_user: APIUser) -> str:
    user_id = getattr(current_user, "id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authenticated user not found")
    return user_id

@router.get("/marketplace/listings")
async def get_listings(
    category: Optional[str] = None,
    item_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "recent",
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """Get marketplace listings with filters"""
    try:
        # Build query
        query = db.query(MarketplaceListing).filter(
            MarketplaceListing.status == "active"
        )
        
        # Apply filters
        if category:
            query = query.filter(MarketplaceListing.category == category)
        if item_type:
            query = query.filter(MarketplaceListing.item_type == item_type)
        if min_price:
            query = query.filter(MarketplaceListing.price >= min_price)
        if max_price:
            query = query.filter(MarketplaceListing.price <= max_price)
        
        # Get total count before pagination
        total = query.count()
        
        # Sort
        if sort_by == "price_low":
            query = query.order_by(MarketplaceListing.price.asc())
        elif sort_by == "price_high":
            query = query.order_by(MarketplaceListing.price.desc())
        elif sort_by == "popular":
            query = query.order_by(MarketplaceListing.downloads.desc())
        elif sort_by == "rating":
            query = query.order_by(MarketplaceListing.rating.desc())
        else:  # recent
            query = query.order_by(MarketplaceListing.created_at.desc())
        
        # Pagination
        offset = (page - 1) * page_size
        listings = query.offset(offset).limit(page_size).all()
        
        # Convert to response format
        listings_data = []
        for listing in listings:
            listings_data.append({
                "id": listing.id,
                "seller_id": listing.seller_id,
                "seller_name": listing.seller.display_name,
                "title": listing.title,
                "description": listing.description,
                "category": listing.category,
                "item_type": listing.item_type,
                "price": float(listing.price),
                "complexity_score": listing.complexity_score,
                "preview_images": listing.preview_images or [],
                "demo_url": listing.demo_url,
                "downloads": listing.downloads,
                "rating": float(listing.rating),
                "status": listing.status,
                "created_at": listing.created_at.isoformat() if listing.created_at else None
            })
        
        return {
            "listings": listings_data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except Exception as e:
        logger.error(f"Error fetching listings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch listings: {str(e)}")

@router.get("/marketplace/listings/{listing_id}")
async def get_listing(listing_id: int, db: Session = Depends(get_db)):
    """Get single listing details"""
    try:
        listing = db.query(MarketplaceListing).filter(
            MarketplaceListing.id == listing_id
        ).first()
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return {
            "id": listing.id,
            "seller_id": listing.seller_id,
            "seller_name": listing.seller.display_name,
            "title": listing.title,
            "description": listing.description,
            "category": listing.category,
            "item_type": listing.item_type,
            "price": float(listing.price),
            "complexity_score": listing.complexity_score,
            "preview_images": listing.preview_images or [],
            "demo_url": listing.demo_url,
            "config_data": listing.config_data or {},
            "downloads": listing.downloads,
            "rating": float(listing.rating),
            "status": listing.status,
            "created_at": listing.created_at.isoformat() if listing.created_at else None,
            "updated_at": listing.updated_at.isoformat() if listing.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching listing {listing_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch listing: {str(e)}")

@router.post("/marketplace/listings")
async def create_listing(
    listing: ListingCreate,
    db: Session = Depends(get_db),
    current_user: APIUser = Depends(get_current_user)
):
    """Create a new marketplace listing"""
    try:
        user_id = _require_user_id(current_user)
        display_name = current_user.email or current_user.username

        # Get or create seller for user
        seller = db.query(Seller).filter(Seller.user_id == user_id).first()
        if not seller:
            # Create seller if doesn't exist
            seller = Seller(
                user_id=user_id,
                display_name=display_name,
                bio=None,
                rating=0.00,
                total_sales=0,
                total_revenue=0.00
            )
            db.add(seller)
            db.flush()  # Get seller.id
        
        # Create listing
        new_listing = MarketplaceListing(
            seller_id=seller.id,
            title=listing.title,
            description=listing.description,
            category=listing.category,
            item_type=listing.item_type,
            price=listing.price,
            complexity_score=listing.complexity_score or 1,
            preview_images=listing.preview_images or [],
            demo_url=listing.demo_url,
            config_data=listing.config_data or {},
            downloads=0,
            rating=0.00,
            status="active"
        )
        
        db.add(new_listing)
        db.commit()
        db.refresh(new_listing)
        
        return {
            "listing": {
                "id": new_listing.id,
                "seller_id": new_listing.seller_id,
                "seller_name": seller.display_name,
                "title": new_listing.title,
                "description": new_listing.description,
                "category": new_listing.category,
                "item_type": new_listing.item_type,
                "price": float(new_listing.price),
                "complexity_score": new_listing.complexity_score,
                "preview_images": new_listing.preview_images or [],
                "demo_url": new_listing.demo_url,
                "downloads": new_listing.downloads,
                "rating": float(new_listing.rating),
                "status": new_listing.status,
                "created_at": new_listing.created_at.isoformat() if new_listing.created_at else None
            },
            "message": "Listing created successfully"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating listing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create listing: {str(e)}")

@router.post("/marketplace/purchase")
async def purchase_item(
    purchase: PurchaseRequest,
    db: Session = Depends(get_db),
    current_user: APIUser = Depends(get_current_user)
):
    """Purchase an item from marketplace"""
    try:
        user_id = _require_user_id(current_user)

        # Get listing
        listing = db.query(MarketplaceListing).filter(
            MarketplaceListing.id == purchase.listing_id,
            MarketplaceListing.status == "active"
        ).first()
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Prevent self-purchase
        if listing.seller.user_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot purchase your own listing")
        
        # Calculate fees (15% platform commission)
        total_amount = float(listing.price)
        platform_fee = total_amount * 0.15
        seller_amount = total_amount - platform_fee
        
        if not settings.stripe_secret_key:
            raise HTTPException(
                status_code=503,
                detail="Stripe is not configured for marketplace purchases"
            )

        stripe.api_key = settings.stripe_secret_key
        amount_cents = int(
            (Decimal(str(total_amount)) * Decimal("100")).quantize(
                Decimal("1"),
                rounding=ROUND_HALF_UP
            )
        )
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=settings.marketplace_currency,
                payment_method=purchase.payment_method_id,
                confirm=True,
                metadata={
                    "listing_id": str(listing.id),
                    "buyer_id": str(user_id),
                    "seller_id": str(listing.seller_id)
                }
            )
        except stripe.error.StripeError as exc:
            logger.error(f"Stripe payment failed: {exc}", exc_info=True)
            raise HTTPException(
                status_code=502,
                detail="Payment processing failed"
            )

        payment_status = payment_intent.status
        purchase_status = "completed" if payment_status == "succeeded" else "pending"
        
        # Create purchase record
        purchase_record = MarketplacePurchase(
            listing_id=purchase.listing_id,
            buyer_id=user_id,
            seller_id=listing.seller_id,
            amount=total_amount,
            platform_fee=platform_fee,
            seller_amount=seller_amount,
            stripe_payment_id=payment_intent.id,
            status=purchase_status
        )
        
        db.add(purchase_record)
        
        if purchase_status == "completed":
            # Update listing downloads
            listing.downloads += 1
            
            # Update seller stats
            seller = listing.seller
            seller.total_sales += 1
            seller.total_revenue += seller_amount
        
        db.commit()
        db.refresh(purchase_record)
        
        message = (
            "Purchase completed successfully"
            if purchase_status == "completed"
            else "Purchase initiated; payment confirmation required"
        )

        return {
            "purchase": {
                "id": purchase_record.id,
                "listing_id": purchase_record.listing_id,
                "buyer_id": purchase_record.buyer_id,
                "seller_id": purchase_record.seller_id,
                "amount": float(purchase_record.amount),
                "platform_fee": float(purchase_record.platform_fee),
                "seller_amount": float(purchase_record.seller_amount),
                "status": purchase_record.status,
                "created_at": purchase_record.created_at.isoformat() if purchase_record.created_at else None
            },
            "payment": {
                "status": payment_status,
                "client_secret": payment_intent.client_secret
            },
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing purchase: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process purchase: {str(e)}")

@router.get("/marketplace/my-listings")
async def get_my_listings(
    db: Session = Depends(get_db),
    current_user: APIUser = Depends(get_current_user)
):
    """Get current user's listings"""
    try:
        user_id = _require_user_id(current_user)

        # Get seller for user
        seller = db.query(Seller).filter(Seller.user_id == user_id).first()
        if not seller:
            return {"listings": []}
        
        listings = db.query(MarketplaceListing).filter(
            MarketplaceListing.seller_id == seller.id
        ).order_by(MarketplaceListing.created_at.desc()).all()
        
        listings_data = []
        for listing in listings:
            listings_data.append({
                "id": listing.id,
                "seller_id": listing.seller_id,
                "seller_name": seller.display_name,
                "title": listing.title,
                "description": listing.description,
                "category": listing.category,
                "item_type": listing.item_type,
                "price": float(listing.price),
                "complexity_score": listing.complexity_score,
                "preview_images": listing.preview_images or [],
                "demo_url": listing.demo_url,
                "downloads": listing.downloads,
                "rating": float(listing.rating),
                "status": listing.status,
                "created_at": listing.created_at.isoformat() if listing.created_at else None
            })
        
        return {"listings": listings_data}
    except Exception as e:
        logger.error(f"Error fetching user listings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch listings: {str(e)}")

@router.get("/marketplace/my-purchases")
async def get_my_purchases(
    db: Session = Depends(get_db),
    current_user: APIUser = Depends(get_current_user)
):
    """Get current user's purchases"""
    try:
        user_id = _require_user_id(current_user)

        purchases = db.query(MarketplacePurchase).filter(
            MarketplacePurchase.buyer_id == user_id
        ).order_by(MarketplacePurchase.created_at.desc()).all()
        
        purchases_data = []
        for purchase in purchases:
            purchases_data.append({
                "id": purchase.id,
                "listing_id": purchase.listing_id,
                "listing_title": purchase.listing.title,
                "seller_id": purchase.seller_id,
                "seller_name": purchase.seller.display_name,
                "amount": float(purchase.amount),
                "platform_fee": float(purchase.platform_fee),
                "seller_amount": float(purchase.seller_amount),
                "status": purchase.status,
                "created_at": purchase.created_at.isoformat() if purchase.created_at else None
            })
        
        return {"purchases": purchases_data}
    except Exception as e:
        logger.error(f"Error fetching user purchases: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch purchases: {str(e)}")

@router.get("/marketplace/seller-stats")
async def get_seller_stats(
    db: Session = Depends(get_db),
    current_user: APIUser = Depends(get_current_user)
):
    """Get seller statistics"""
    try:
        user_id = _require_user_id(current_user)

        seller = db.query(Seller).filter(Seller.user_id == user_id).first()
        if not seller:
            return {
                "total_sales": 0,
                "total_revenue": 0.0,
                "rating": 0.0,
                "active_listings": 0
            }
        
        active_listings = db.query(MarketplaceListing).filter(
            and_(
                MarketplaceListing.seller_id == seller.id,
                MarketplaceListing.status == "active"
            )
        ).count()
        
        return {
            "total_sales": seller.total_sales,
            "total_revenue": float(seller.total_revenue),
            "rating": float(seller.rating),
            "active_listings": active_listings
        }
    except Exception as e:
        logger.error(f"Error fetching seller stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch seller stats: {str(e)}")

@router.delete("/marketplace/listings/{listing_id}")
async def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: APIUser = Depends(get_current_user)
):
    """Delete a listing (soft delete by setting status to 'removed')"""
    try:
        user_id = _require_user_id(current_user)

        listing = db.query(MarketplaceListing).filter(
            MarketplaceListing.id == listing_id
        ).first()
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        # Verify ownership
        if listing.seller.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this listing")
        
        # Soft delete
        listing.status = "removed"
        db.commit()
        
        return {"message": "Listing deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting listing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete listing: {str(e)}")
