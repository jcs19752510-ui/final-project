import asyncio
from logging.config import fileConfig

from alembic import context

from app.config import settings
from app.db import Base, engine
from app import models  # noqa: F401  (모델 전부 import되어야 autogenerate가 인식)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    # app.db.engine을 그대로 재사용 — DB_SSL_REQUIRE(Neon 등 관리형 Postgres
    # 대응) 커넥션 설정이 여기서도 똑같이 적용되어야 하므로 별도로 새
    # 엔진을 만들지 않는다(중복 시 설정이 어긋날 위험).
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
