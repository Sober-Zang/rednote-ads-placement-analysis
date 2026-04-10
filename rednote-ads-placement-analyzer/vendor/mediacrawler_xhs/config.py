# -*- coding: utf-8 -*-
"""Runtime configuration for the internalized Xiaohongshu crawler."""

from __future__ import annotations

from pathlib import Path

# Platform basics
PLATFORM = "xhs"
KEYWORDS = ""
LOGIN_TYPE = "qrcode"
COOKIES = ""
CRAWLER_TYPE = "detail"

# Proxy / browser
ENABLE_IP_PROXY = False
IP_PROXY_POOL_COUNT = 2
IP_PROXY_PROVIDER_NAME = "kuaidaili"
HEADLESS = False
SAVE_LOGIN_STATE = True
ENABLE_CDP_MODE = False
CDP_DEBUG_PORT = 9222
CUSTOM_BROWSER_PATH = ""
CDP_HEADLESS = False
BROWSER_LAUNCH_TIMEOUT = 60
AUTO_CLOSE_BROWSER = True

# Data capture
SAVE_DATA_OPTION = "json"
SAVE_DATA_PATH = ""
USER_DATA_DIR = "%s_user_data_dir"
START_PAGE = 1
CRAWLER_MAX_NOTES_COUNT = 20
MAX_CONCURRENCY_NUM = 1
ENABLE_GET_MEIDAS = True
ENABLE_GET_COMMENTS = True
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 500
ENABLE_GET_SUB_COMMENTS = True
ENABLE_GET_WORDCLOUD = True
CRAWLER_MAX_SLEEP_SEC = 1
DISABLE_SSL_VERIFY = False

# Cache / database compatibility values required by donor modules
REDIS_DB_HOST = "127.0.0.1"
REDIS_DB_PWD = "123456"
REDIS_DB_PORT = 6379
REDIS_DB_NUM = 0
CACHE_TYPE_REDIS = "memory"
CACHE_TYPE_MEMORY = "memory"

# Xiaohongshu detail mode
SORT_TYPE = "popularity_descending"
XHS_SPECIFIED_NOTE_URL_LIST: list[str] = []
XHS_CREATOR_ID_LIST: list[str] = []

# Word cloud
CUSTOM_WORDS: dict[str, str] = {}
STOP_WORDS_FILE = ""
FONT_PATH = ""

# Product runtime paths
PRODUCT_ROOT = Path(__file__).resolve().parents[2]
RUN_OUTPUT_DIR = ""
RUNTIME_DIR = ""
LOGIN_STATE_DIR = str((PRODUCT_ROOT.parent / "xhs_user_data_dir").resolve())
RUN_ID = ""
TASK_SLUG = ""

# Runtime behavior
REQUIRE_LOGIN = False
ALLOW_ANONYMOUS_HTML_FALLBACK = True
LOGIN_STATE_CONFIRMED = False


def apply_runtime_config(values: dict) -> None:
    """Update module globals with runtime values."""
    globals().update(values)
