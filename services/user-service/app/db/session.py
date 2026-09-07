from app.core import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

engine = create_async_engine(settings.database_url, echo = False)
async_session_local = async_sessionmaker(bind = engine, class_= AsyncSession, expire_on_commit = False)

'''Alembic is handling it, so there is no need of it'''
# async def init_db():
#     ''' It creates all the tables in the database'''
#     async with engine.begin() as conn:
#         await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    ''' It returns a async session '''
    async with async_session_local() as session:
        yield session