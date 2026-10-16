"""Alembic env.py — async setup برای PostgreSQL + asyncpg."""

import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ─── load .env ───
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# ─── alembic config ───
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ─── override sqlalchemy.url از env ───
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL تنظیم نشده")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# ─── import models + metadata ───
from app.infrastructure.db.base import Base
from app.infrastructure.db.models import (  # noqa: F401
    RegisterAttempt,
    User,
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline — تولید SQL بدون اتصال."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
