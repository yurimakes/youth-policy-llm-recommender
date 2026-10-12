"""컨테이너 내부에서 DB를 포함한 API 준비 상태만 짧게 점검합니다."""

from __future__ import annotations

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from youth_policy.api_smoke import LocalApiClient, SmokeError


def main() -> int:
    """원문 응답이나 설정을 출력하지 않고 Docker healthcheck 종료 코드만 반환합니다."""
    try:
        port = int(os.environ.get("PORT", "8000"))
        if not 1 <= port <= 65535:
            return 1
        result = LocalApiClient(f"http://127.0.0.1:{port}", timeout=2).request("/ready")
        return 0 if (result.get("status") == "ready" and type(result.get("policy_count")) is int
                     and result["policy_count"] > 0) else 1
    except (SmokeError, ValueError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
