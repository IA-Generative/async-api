from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import AsyncSessionLocal
from listener.core.logger import logger

ctx_db_session: ContextVar[AsyncSession] = ContextVar("db_session")


# Dynamic proxy for AsyncSession
class TaskAwareAsyncSession:
    @staticmethod
    def _get_wrapped_session() -> AsyncSession:
        # New task: new session
        try:
            return ctx_db_session.get()
        except Exception:
            session: AsyncSession = AsyncSessionLocal()
            ctx_db_session.set(session)
            logger.debug(f"Task session {id(session)} created")
            return session

    def __getattr__(self, name: str) -> str:
        return getattr(self._get_wrapped_session(), name)
