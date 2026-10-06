"""test_ontong_client.py

온통청년 API 클라이언트의 저장과 오류 처리를 테스트합니다.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.config import ConfigurationError, get_ontong_api_key
from youth_policy.ontong_client import (
    ONTONG_POLICY_ENDPOINT,
    OntongEmptyResponseError,
    OntongHttpError,
    OntongNetworkError,
    fetch_ontong_policies,
)


def load_fetch_script():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "fetch_ontong_policies.py"
    spec = importlib.util.spec_from_file_location("fetch_ontong_policies_script", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(
        self,
        *,
        content: bytes,
        status_code: int = 200,
        content_type: str | None = "application/json",
    ) -> None:
        self.content = content
        self.status_code = status_code
        self.headers = {}
        if content_type is not None:
            self.headers["Content-Type"] = content_type


class FakeRequester:
    def __init__(self, response: FakeResponse | None = None) -> None:
        self.response = response or FakeResponse(content=b'{"resultCode":200}')
        self.calls: list[dict[str, object]] = []

    def get(
        self,
        url: str,
        *,
        params: dict[str, object],
        timeout: float,
    ) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.response


class RaisingRequester:
    def get(
        self,
        url: str,
        *,
        params: dict[str, object],
        timeout: float,
    ) -> FakeResponse:
        raise requests.ConnectionError("network unavailable")


def test_get_ontong_api_key_prefers_environment_over_streamlit_secrets(tmp_path):
    secrets_path = tmp_path / "secrets.toml"
    secrets_path.write_text('ONTONG_API_KEY = "secret-key"\n', encoding="utf-8")

    assert (
        get_ontong_api_key(
            environ={"ONTONG_API_KEY": "env-key"},
            secrets_path=secrets_path,
        )
        == "env-key"
    )


def test_get_ontong_api_key_reads_streamlit_secrets_when_env_missing(tmp_path):
    secrets_path = tmp_path / "secrets.toml"
    secrets_path.write_text('ONTONG_API_KEY = "secret-key"\n', encoding="utf-8")

    assert (
        get_ontong_api_key(environ={}, secrets_path=secrets_path)
        == "secret-key"
    )


def test_get_ontong_api_key_raises_without_secret(tmp_path):
    with pytest.raises(ConfigurationError, match="ONTONG_API_KEY"):
        get_ontong_api_key(
            environ={},
            secrets_path=tmp_path / "missing.toml",
        )


def test_fetch_script_help_does_not_read_secret_or_call_api(monkeypatch, capsys):
    script = load_fetch_script()

    def fail_if_called(*args, **kwargs):
        pytest.fail("API key loading or API fetch should not run for --help.")

    monkeypatch.setattr(script, "get_ontong_api_key", fail_if_called)
    monkeypatch.setattr(script, "fetch_ontong_policies", fail_if_called)

    with pytest.raises(SystemExit) as exc_info:
        script.main(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "--page-num" in output
    assert "--page-size" in output
    assert "--page-type" in output
    assert "--rtn-type" in output
    assert "--output-dir" in output
    assert "--timeout" in output


def test_fetch_ontong_policies_saves_raw_json_and_metadata(tmp_path):
    requester = FakeRequester(
        FakeResponse(
            content=b'{"resultCode":200,"result":{"youthPolicyList":[]}}',
            content_type="application/json; charset=utf-8",
        )
    )

    result = fetch_ontong_policies(
        api_key="test-key",
        output_dir=tmp_path,
        timeout=3.5,
        requester=requester,
    )

    assert result.response_format == "json"
    assert result.response_size_bytes == 50
    assert result.raw_path.suffix == ".json"
    assert result.raw_path.read_bytes() == (
        b'{"resultCode":200,"result":{"youthPolicyList":[]}}'
    )
    assert requester.calls == [
        {
            "url": ONTONG_POLICY_ENDPOINT,
            "params": {
                "apiKeyNm": "test-key",
                "pageNum": 1,
                "pageSize": 10,
                "pageType": 1,
                "rtnType": "json",
            },
            "timeout": 3.5,
        }
    ]

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["endpoint"] == ONTONG_POLICY_ENDPOINT
    assert metadata["pageNum"] == 1
    assert metadata["pageSize"] == 10
    assert metadata["pageType"] == 1
    assert metadata["rtnType"] == "json"
    assert metadata["response_format"] == "json"
    assert metadata["response_size_bytes"] == 50
    assert metadata["raw_file"] == result.raw_path.name
    assert "apiKeyNm" not in metadata
    assert "test-key" not in result.metadata_path.read_text(encoding="utf-8")


def test_fetch_ontong_policies_detects_xml_from_content_start(tmp_path):
    requester = FakeRequester(
        FakeResponse(
            content=b"  <response></response>",
            content_type="text/plain",
        )
    )

    result = fetch_ontong_policies(
        api_key="test-key",
        output_dir=tmp_path,
        requester=requester,
    )

    assert result.response_format == "xml"
    assert result.raw_path.suffix == ".xml"


def test_fetch_ontong_policies_uses_unique_file_names(tmp_path):
    requester = FakeRequester(FakeResponse(content=b'{"ok":true}'))

    first = fetch_ontong_policies(
        api_key="test-key",
        output_dir=tmp_path,
        requester=requester,
    )
    second = fetch_ontong_policies(
        api_key="test-key",
        output_dir=tmp_path,
        requester=requester,
    )

    assert first.raw_path != second.raw_path
    assert first.metadata_path != second.metadata_path
    assert first.raw_path.exists()
    assert second.raw_path.exists()


def test_fetch_ontong_policies_raises_for_http_error(tmp_path):
    requester = FakeRequester(FakeResponse(content=b"error", status_code=500))

    with pytest.raises(OntongHttpError, match="HTTP status 500"):
        fetch_ontong_policies(
            api_key="test-key",
            output_dir=tmp_path,
            requester=requester,
        )


def test_fetch_ontong_policies_raises_for_network_error(tmp_path):
    with pytest.raises(OntongNetworkError, match="Could not connect"):
        fetch_ontong_policies(
            api_key="test-key",
            output_dir=tmp_path,
            requester=RaisingRequester(),
        )


def test_fetch_ontong_policies_raises_for_empty_response(tmp_path):
    requester = FakeRequester(FakeResponse(content=b"  \n"))

    with pytest.raises(OntongEmptyResponseError, match="empty response"):
        fetch_ontong_policies(
            api_key="test-key",
            output_dir=tmp_path,
            requester=requester,
        )
