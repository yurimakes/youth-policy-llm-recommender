"""export_intake_schemas.py

UI 팀원이 참고할 Pydantic JSON Schema 계약 파일을 재생성합니다.
"""

from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.api_schemas import IntakeResponse, StartRequest, TransitionRequest


def main() -> None:
    folder = Path(__file__).resolve().parents[1] / "docs/api/schemas"
    folder.mkdir(parents=True, exist_ok=True)
    for name, model in (
        ("start-request.json", StartRequest), ("transition-request.json", TransitionRequest),
        ("intake-response.json", IntakeResponse),
    ):
        (folder / name).write_text(
            json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
