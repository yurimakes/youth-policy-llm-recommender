"""config.py

환경 변수와 Streamlit secrets에서 애플리케이션 설정값을 읽습니다.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping


class ConfigurationError(RuntimeError):
    """필수 설정값을 안전하게 읽을 수 없을 때 발생합니다."""


def get_ontong_api_key(
    *,
    environ: Mapping[str, str] | None = None,
    secrets_path: Path | None = None,
) -> str:
    env = environ if environ is not None else os.environ
    env_value = env.get("ONTONG_API_KEY")
    if env_value is not None and env_value.strip():
        return env_value.strip()

    streamlit_secrets_path = secrets_path or Path(".streamlit") / "secrets.toml"
    secrets_value = _read_top_level_secret(
        streamlit_secrets_path,
        "ONTONG_API_KEY",
    )
    if secrets_value is not None and secrets_value.strip():
        return secrets_value.strip()

    raise ConfigurationError(
        "ONTONG_API_KEY is required. Set it as an environment variable or in "
        ".streamlit/secrets.toml."
    )


def _read_top_level_secret(path: Path, key: str) -> str | None:
    if not path.exists():
        return None

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigurationError("Could not read Streamlit secrets file.") from exc

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        found_key, raw_value = stripped.split("=", 1)
        if found_key.strip() != key:
            continue

        return _parse_secret_value(raw_value)

    return None


def _parse_secret_value(raw_value: str) -> str:
    value = raw_value.split("#", 1)[0].strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
