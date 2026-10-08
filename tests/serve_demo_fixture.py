"""브라우저 회귀용 실제 FastAPI를 격리된 합성 정책으로 실행합니다."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from youth_policy.api_app import create_app
from test_intake import policy, TODAY

app = create_app(policy_provider=lambda: (policy(),), date_provider=lambda: TODAY)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
