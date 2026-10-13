"""정책 DB를 읽기 전용으로 점검한 뒤 API와 같은 origin의 화면을 실행합니다."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from youth_policy.api_config import load_api_settings
from youth_policy.policy_repository import PolicyDataUnavailable, load_policies_readonly


def port_number(value: str) -> int:
    """플랫폼 PORT와 CLI 포트에 같은 검사를 적용합니다."""
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer from 1 to 65535") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be an integer from 1 to 65535")
    return port


def main(argv: Sequence[str] | None = None) -> int:
    """누락·빈 DB는 종료 코드 2로 알리고 경로·키·레코드 원문은 출력하지 않습니다."""
    parser = argparse.ArgumentParser(description="Start the same-origin Intake API after a read-only data check.")
    parser.add_argument("--host", default=os.environ.get("API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=port_number, default=os.environ.get("PORT", "8000"))
    args = parser.parse_args(argv)
    try:
        records = load_policies_readonly(load_api_settings().policy_db_path)
    except (PolicyDataUnavailable, ValueError):
        print("API not started: check policy database and API configuration.", file=sys.stderr)
        return 2
    if not records:
        print("API not started: policy database is empty.", file=sys.stderr)
        return 2
    import uvicorn

    uvicorn.run("api:app", app_dir=str(ROOT), host=args.host, port=args.port,
                proxy_headers=False, access_log=False, server_header=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
