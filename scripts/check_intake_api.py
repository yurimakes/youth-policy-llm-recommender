"""실행 중인 로컬 API의 HTTP 흐름을 합성 입력으로 점검하는 CLI입니다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.api_smoke import LocalApiClient, run_smoke


def main(argv: Sequence[str] | None = None) -> int:
    """점검 요약만 출력하며 실제 사용자 답변·원문 응답·파일을 저장하지 않습니다."""
    parser = argparse.ArgumentParser(description="Check a running local Intake API with synthetic answers.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--require-detail", action="store_true", help="Return exit code 2 if detail checks are skipped.")
    args = parser.parse_args(argv)
    try:
        client = LocalApiClient(args.base_url, timeout=args.timeout)
    except ValueError:
        print("Invalid local URL or timeout.", file=sys.stderr)
        return 1
    checks = run_smoke(client)
    print(json.dumps({"checks": [vars(check) for check in checks],
                      "passed": sum(c.status == "PASS" for c in checks),
                      "failed": sum(c.status == "FAIL" for c in checks),
                      "skipped": sum(c.status == "SKIP" for c in checks),
                      "warnings": sum(c.status == "WARN" for c in checks)}, indent=2))
    if any(c.status == "FAIL" for c in checks):
        return 1
    return 2 if args.require_detail and any(c.status == "SKIP" for c in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
