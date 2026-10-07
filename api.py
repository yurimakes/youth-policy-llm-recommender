"""api.py

기존 Streamlit과 분리된 로컬 개발용 FastAPI의 진입점입니다.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from youth_policy.api_app import create_app

app = create_app()
