import httpx
import asyncio
import logging
from sqlalchemy.future import select
from app.models import Site, CheckLog
from app.database import AsyncSessionLocal

logger = logging.getLogger("monitor")

REQUEST_TIMEOUT = 10.0  # секунд на один запит


async def check_site_status(url: str) -> int:
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, follow_redirects=True)
            return response.status_code
    except httpx.HTTPError:
        return 0


async def check_and_log(site: Site) -> tuple[Site, int]:
    status = await check_site_status(site.url)
    return site, status


async def start_monitoring():
    while True:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Site))
            sites = result.scalars().all()


            results = await asyncio.gather(
                *[check_and_log(site) for site in sites]
            )

            for site, status in results:
                is_online = (status == 200)
                site.status_code = status
                site.is_online = is_online
                db.add(site)

                new_log = CheckLog(
                    site_id=site.id,
                    status_code=status,
                    is_online=is_online,
                )
                db.add(new_log)

                if is_online:
                    logger.info("Сайт %s (%s) повернув статус: %s", site.name, site.url, status)
                else:
                    logger.warning("Сайт %s (%s) недоступний, статус: %s", site.name, site.url, status)

            await db.commit()

        await asyncio.sleep(10)