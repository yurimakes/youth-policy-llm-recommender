"""api_config.py

로컬 API의 정책 DB 경로·허용 origin과 한국 기준 날짜를 구성합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import os
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse


@dataclass(frozen=True)
class ApiSettings:
    policy_db_path: Path
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://localhost:3000")


def load_api_settings(
    *, environ: Mapping[str, str] | None = None, project_root: Path | None = None
) -> ApiSettings:
    env = os.environ if environ is None else environ
    root = project_root or Path(__file__).resolve().parents[2]
    path = Path(env.get("POLICY_DB_PATH", "data/processed/policies.sqlite3"))
    if not path.is_absolute():
        path = root / path
    origins = tuple(x.strip() for x in env.get(
        "API_CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",") if x.strip())
    for origin in origins:
        parsed = urlparse(origin)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or "*" in parsed.netloc or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password):
            raise ValueError("API_CORS_ORIGINS must contain exact http(s) origins")
        try:
            parsed.port
        except ValueError as exc:
            raise ValueError("API_CORS_ORIGINS contains an invalid port") from exc
    return ApiSettings(path, origins)


def korea_today() -> date:
    return datetime.now(timezone(timedelta(hours=9))).date()
