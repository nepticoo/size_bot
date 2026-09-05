from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import LocalStorage
from app.models.job import Job
from app.models.request import MeasureRequest

_storage = LocalStorage()


async def delete_photo(job: Job, db: AsyncSession) -> None:
    request_id = job.payload.get("request_id")
    request = await db.get(MeasureRequest, request_id)
    if request is None or request.photo_path is None:
        return
    _storage.delete(request.photo_path)
    request.photo_path = None


HANDLERS = {
    "delete_photo": delete_photo,
}
