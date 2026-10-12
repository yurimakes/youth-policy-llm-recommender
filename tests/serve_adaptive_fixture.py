"""Serve an isolated synthetic catalogue for adaptive browser regression."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from test_adaptive_questions import TODAY, example_policies
from youth_policy.api_app import create_app


app = create_app(policy_provider=example_policies, date_provider=lambda: TODAY)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8767)
