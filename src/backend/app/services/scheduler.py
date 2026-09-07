import logging
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import AsyncSessionLocal
from app.services.user_service import purge_expired_users

logger = logging.getLogger("aimock.scheduler")


async def _run_purge_job() -> None:
    async with AsyncSessionLocal() as db:
        purged_ids = await purge_expired_users(db)
    if purged_ids:
        Path("logs").mkdir(exist_ok=True)
        logger.info("계정 파기 %d건: %s", len(purged_ids), purged_ids)


def create_scheduler() -> AsyncIOScheduler:
    """ADR-006: 매일 1회 purge_at 경과 사용자를 물리 삭제."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(_run_purge_job, "interval", days=1, id="purge_expired_users")
    return scheduler
