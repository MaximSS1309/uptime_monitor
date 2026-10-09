from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Site, CheckLog
from app.schemas import SiteCreate, SiteUpdate, SiteOut, CheckLogOut

router = APIRouter(prefix="/sites", tags=["sites"])


@router.post("/", response_model=SiteOut)
async def create_site(site_data: SiteCreate, db: AsyncSession = Depends(get_db)):
    new_site = Site(name=site_data.name, url=str(site_data.url))
    db.add(new_site)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Site with this URL already exists"
        )
    await db.refresh(new_site)
    return new_site


@router.get("/", response_model=list[SiteOut])
async def get_all_sites(
    skip: int = Query(0, ge=0, description="Скільки записів пропустити"),
    limit: int = Query(50, ge=1, le=200, description="Скільки записів повернути"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).order_by(Site.id).offset(skip).limit(limit)
    )
    sites = result.scalars().all()
    return sites


@router.get("/{site_id}", response_model=SiteOut)
async def get_site(site_id: int, db: AsyncSession = Depends(get_db)):
    site = await db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.put("/{site_id}", response_model=SiteOut)
async def update_site(
    site_id: int, site_data: SiteUpdate, db: AsyncSession = Depends(get_db)
):
    site = await db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    if site_data.name is not None:
        site.name = site_data.name
    if site_data.url is not None:
        site.url = str(site_data.url)

    db.add(site)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Site with this URL already exists"
        )
    await db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=204)
async def delete_site(site_id: int, db: AsyncSession = Depends(get_db)):
    site = await db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    await db.delete(site)


@router.get("/{site_id}/logs", response_model=list[CheckLogOut])
async def get_site_log(
    site_id: int,
    skip: int = Query(0, ge=0, description="Скільки записів пропустити"),
    limit: int = Query(50, ge=1, le=200, description="Скільки записів повернути"),
    db: AsyncSession = Depends(get_db),
):
    site = await db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")

    result = await db.execute(
        select(CheckLog)
        .where(CheckLog.site_id == site_id)
        .order_by(CheckLog.checked_at.desc())
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    return logs