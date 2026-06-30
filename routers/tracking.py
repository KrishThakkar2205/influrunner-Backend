from accessToken import VerifyAccessToken
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta

from database import get_db
from models import PortfolioViews
from accessToken import get_current_user 

router = APIRouter(prefix="/analytics")

@router.get("/portoflio/summary/{profile_id}")
def get_portoflio_summary(profile_id : str, db: Session = Depends(get_db), token : str = Depends(get_current_user)):
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Unauthorized")
    
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)

    base_query = db.query(PortfolioViews).filter(
        PortfolioViews.influencer_id == profile_id,
        PortfolioViews.viewed_at >= month_ago
    )

    total_views = base_query.count()
    unique_views = base_query.filter(
        PortfolioViews.is_unique == True,
    ).count()

    repeat_views = total_views - unique_views

    return {
        "period": "last_30_days",
        "total_views": total_views,
        "unique_views": unique_views,
        "repeat_views": repeat_views
    }


@router.get("/portfolio/viewed/source/{profile_id}")
def get_portfolio_viewed_source(profile_id : str, db: Session = Depends(get_db), token : str = Depends(get_current_user)):
    user_id = VerifyAccessToken(token)
    if not user_id:
        return Response(status_code=401, content="Unauthorized")
    
    month_ago = datetime.utcnow() - timedelta(days=30)
    
    results = db.query(
        PortfolioViews.utm_source.label("source"),
        func.count(PortfolioViews.id).label("views")
    ).filter(
        PortfolioViews.portfolio_id == profile_id,
        PortfolioViews.viewed_at >= month_ago
    ).group_by(
        PortfolioViews.utm_source
    ).order_by(
        func.count(PortfolioViews.id).desc()
    ).all()

    total = sum(r.views for r in results)

    source_data = [
        {
            "source" : r.source or "unknown",
            "views" : r.views,
            "percentage" : round((r.views / total) * 100, 2) if total > 0 else 0
        }
        for r in results
    ]
    
    return {
        "period": "last_30_days",
        "sources": source_data
    }