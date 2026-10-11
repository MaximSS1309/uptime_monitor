from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.auth import get_current_user
from app.database import get_db
from app.models import Site, CheckLog, User
from app.schemas import SiteCreate, SiteUpdate, SiteOut, CheckLogOut

router = APIRouter(prefix="/sites", tags=["sites"])


async def get_owned_site(db: AsyncSession, site_id: int, user: User) -> Site:
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.owner_id == user.id)
    )
    site = result.scalar_one_or_none()
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    return site


@router.post("/", response_model=SiteOut)
async def create_site(
    site_data: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_site = Site(
        name=site_data.name,
        url=str(site_data.url),
        owner_id=current_user.id,
    )
    db.add(new_site)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="You already monitor a site with this URL"
        )
    await db.refresh(new_site)
    return new_site


@router.get("/", response_model=list[SiteOut])
async def get_all_sites(
    skip: int = Query(0, ge=0, description="Скільки записів пропустити"),
    limit: int = Query(50, ge=1, le=200, description="Скільки записів повернути"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Site)
        .where(Site.owner_id == current_user.id)
        .order_by(Site.id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/{site_id}", response_model=SiteOut)
async def get_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_owned_site(db, site_id, current_user)


@router.put("/{site_id}", response_model=SiteOut)
async def update_site(
    site_id: int,
    site_data: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = await get_owned_site(db, site_id, current_user)

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
            status_code=409, detail="You already monitor a site with this URL"
        )
    await db.refresh(site)
    return site


@router.delete("/{site_id}", status_code=204)
async def delete_site(
    site_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    site = await get_owned_site(db, site_id, current_user)
    await db.delete(site)


@router.get("/{site_id}/logs", response_model=list[CheckLogOut])
async def get_site_log(
    site_id: int,
    skip: int = Query(0, ge=0, description="Скільки записів пропустити"),
    limit: int = Query(50, ge=1, le=200, description="Скільки записів повернути"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await get_owned_site(db, site_id, current_user)

    result = await db.execute(
        select(CheckLog)
        .where(CheckLog.site_id == site_id)
        .order_by(CheckLog.checked_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()