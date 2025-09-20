import asyncio
from contextvars import Context

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from listener.core.task_aware_async_session import TaskAwareAsyncSession


def test_session_proxy_call_to_inner_session() -> None:
    session_proxy = TaskAwareAsyncSession()
    # Random call to the subsequent object
    assert session_proxy.is_active


def test_create_session_outside_event_loop() -> None:
    session_proxy = TaskAwareAsyncSession()
    inner1 = session_proxy._get_wrapped_session()
    inner2 = session_proxy._get_wrapped_session()
    assert inner1 == inner2


@pytest.mark.asyncio
async def test_create_session_inside_event_loop() -> None:
    # Same task, same session
    session_proxy = TaskAwareAsyncSession()
    inner1 = session_proxy._get_wrapped_session()
    inner2 = session_proxy._get_wrapped_session()
    assert inner1 == inner2


async def get_inner_session(session_proxy: TaskAwareAsyncSession) -> AsyncSession:
    return session_proxy._get_wrapped_session()


@pytest.mark.asyncio
async def test_create_session_in_new_task() -> None:
    # One session per task
    session_proxy = TaskAwareAsyncSession()
    inner1 = session_proxy._get_wrapped_session()
    inner2 = await asyncio.create_task(get_inner_session(session_proxy), context=Context())
    assert inner1 != inner2


@pytest.mark.asyncio
async def test_create_session_in_new_tasks() -> None:
    # One session per task
    session_proxy = TaskAwareAsyncSession()
    inner1 = await asyncio.create_task(get_inner_session(session_proxy), context=Context())
    inner2 = await asyncio.create_task(get_inner_session(session_proxy), context=Context())
    assert inner1 != inner2
