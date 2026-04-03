# -*- coding: utf-8 -*-
"""Trimmed runtime context vars for the internalized crawler."""

from __future__ import annotations

from asyncio.tasks import Task
from contextvars import ContextVar
from typing import Any, List

request_keyword_var: ContextVar[str] = ContextVar("request_keyword", default="")
crawler_type_var: ContextVar[str] = ContextVar("crawler_type", default="")
comment_tasks_var: ContextVar[List[Task]] = ContextVar("comment_tasks", default=[])
db_conn_pool_var: ContextVar[Any] = ContextVar("db_conn_pool_var", default=None)
source_keyword_var: ContextVar[str] = ContextVar("source_keyword", default="")
