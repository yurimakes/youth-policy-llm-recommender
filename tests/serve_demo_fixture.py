"""브라우저 회귀용 실제 FastAPI를 격리된 합성 정책으로 실행합니다."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from youth_policy.api_app import create_app
from test_intake import policy, TODAY

def select_test_evidence(context: dict) -> dict:
    """Isolated selector fixture; does not call a model or verify an official notice."""
    return {"evidence_ids": [item["evidence_id"] for item in context["evidence"] if item["field"] == "required_documents"]}


app = create_app(policy_provider=lambda: (policy(
    required_documents="테스트용 서류 원문", application_method="테스트용 접수 안내",
    contact="TEST ONLY 문의처"),), date_provider=lambda: TODAY, evidence_selector=select_test_evidence)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
