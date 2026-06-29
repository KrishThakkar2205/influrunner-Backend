from asyncio import timeout
from fastapi import APIRouter,Depends,Request,Response
from sqlalchemy.orm import Session
from database import get_db
from datetime import datetime, timedelta
from models import PortfolioViews
import hashlib
import httpx

router = APIRouter(
    prefix="/portfolio",
    tags=["Portfolio"]
)

async def get_city_from_ip(ip: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://ip-api.co/json/{ip}", timeout = 3.0)
            data = response.json()
            if data["status"] == "success":
                return data.get("city", "Unknown")
            return "Unknown"
    except Exception as e:
        print(e)
        return "Unknown"


def is_unique_visit(db: Session, portfolio_id: str, fingerprint_hash: str) -> bool:
    cutoff = datetime.utcnow() - timedelta(hours=24)
    portfolio_view = db.query(PortfolioViews).filter(
        PortfolioViews.influencer_id == portfolio_id,
        PortfolioViews.fingerprint_hash == fingerprint_hash,
        PortfolioViews.viewed_at >= cutoff
    ).first()
    
    return portfolio_view is None


@router.post("/trackView")
async def track_portfolio_view(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.client.host
        )
        city = await get_city_from_ip(client_ip)
        
        portfolio_id = data.get("portfolio_id")
        fingerprint_hash = data.get("fingerprint_hash")
        utm_source = data.get("utm_source", "direct")
        referrer = data.get("referrer", "direct")
        device_type = data.get("device_type", "desktop")
        
        unique = is_unique_visit(db, portfolio_id, fingerprint_hash)
        
        view = PortfolioViews(
            influencer_id=portfolio_id,
            fingerprint_hash=fingerprint_hash,
            utm_source=utm_source,
            referrer=referrer,
            device_type=device_type,
            city=city,
            is_unique=unique,
            viewed_at=datetime.utcnow()
        )
        db.add(view)
        db.commit()
        
        return Response(status_code=200, content="Portfolio view tracked successfully")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))