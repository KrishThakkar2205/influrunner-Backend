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


def is_unique_visit(db: Session, portfolio_id: int, fingerprint_hash: str) -> bool:
    cutoff = datetime.utcnow() - timedelta(hours=24)
    portfolio_view = db.query(PortfolioViews).filter(
        PortfolioViews.portfolio_id == portfolio_id,
        PortfolioViews.fingerprint_hash == fingerprint_hash,
        PortfolioViews.viewed_at >= cutoff
    ).first()
    
    return portfolio_view is None


@router.post("/trackView")
async def track_portfolio_view(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        client_ip = (
            request.headers.get("x-forwarded-for","").split(",")[0].strip()
            or request.client.host
        )
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()
        city = await get_city_from_ip(client_ip)
        unique = is_unique_visit(db, data["portfolio_id"], data["fingerprint_hash"])
        
        view = PortfolioViews(
            influencer_id=data["influencer_id"],
            portfolio_id=data["portfolio_id"],
            fingerprint_hash=data["fingerprint_hash"],
            ip_hash=ip_hash,
            device_type=data["device_type"],
            city=city,
            unique=unique,
            viewed_at=datetime.utcnow()
        )
        db.add(view)
        db.commit()
        
        return Response(status_code=200, content="Portfolio view tracked successfully")
    except Exception as e:
        print(e)
        return Response(status_code=500, content=str(e))