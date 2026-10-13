"""실제 배포 실행기를 임시 SQLite와 HTTP 서버로 검증합니다. 외부 모델은 호출하지 않습니다."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from test_intake import policy
from run_intake_api import port_number
from youth_policy.api_smoke import DeployedApiClient, LocalApiClient, run_smoke
from youth_policy.sqlite_store import connect_database, initialize_database, upsert_policies


def write_database(path: Path, *, empty: bool = False) -> None:
    """실제 공고가 아닌 테스트 정책만 별도 DB에 씁니다."""
    connection = connect_database(path)
    try:
        initialize_database(connection)
        if not empty:
            # Keep cold-start checks independent of the current calendar date.
            upsert_policies(connection, (replace(policy(), application_start=None, application_end=None,
                                                  required_documents="TEST ONLY recorded documents"),))
    finally:
        connection.close()


def service_environment(database: Path, port: int = 8000) -> dict[str, str]:
    env = dict(os.environ)
    env.update(POLICY_DB_PATH=str(database), PORT=str(port), API_HOST="127.0.0.1",
               API_CORS_ORIGINS="", POLICY_EXPLANATION_AI_ENABLED="0", OPENAI_API_KEY="",
               PYTHONDONTWRITEBYTECODE="1")
    return env


@contextmanager
def launched_service(runtime: Path, database: Path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    env = service_environment(database, port)
    process = subprocess.Popen([sys.executable, str(runtime / "scripts/run_intake_api.py")],
                               cwd=runtime.parent, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail("deployment process exited before readiness")
            try:
                with urlopen(url + "/ready", timeout=0.3) as reply:
                    if reply.status == 200:
                        break
            except (URLError, OSError):
                time.sleep(0.05)
        else:
            pytest.fail("deployment process did not become ready")
        yield url, env
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.mark.parametrize("kind", ["missing", "empty", "invalid"])
def test_startup_rejects_unusable_db_without_creating_it(tmp_path, kind):
    database = tmp_path / "PRIVATE-PATH.sqlite3"
    if kind == "empty":
        write_database(database, empty=True)
    elif kind == "invalid":
        database.write_bytes(b"not SQLite")
    result = subprocess.run([sys.executable, str(ROOT / "scripts/run_intake_api.py")],
                            cwd=tmp_path, env=service_environment(database), capture_output=True, timeout=10)
    assert result.returncode == 2
    assert b"PRIVATE-PATH" not in result.stderr
    assert b"not started" in result.stderr
    if kind == "missing":
        assert not database.exists()


def test_packaged_runtime_starts_from_another_directory_and_serves_real_api(tmp_path):
    # Match the runtime COPY set: no app.py, tests, snapshots, secrets or DB in /app.
    runtime = tmp_path / "app"
    runtime.mkdir()
    shutil.copy2(ROOT / "api.py", runtime / "api.py")
    for directory in ("src", "demo"):
        shutil.copytree(ROOT / directory, runtime / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (runtime / "scripts").mkdir()
    for name in ("run_intake_api.py", "check_readiness.py"):
        shutil.copy2(ROOT / "scripts" / name, runtime / "scripts" / name)
    database = tmp_path / "external.sqlite3"
    write_database(database)
    original = database.read_bytes()
    with launched_service(runtime, database) as (url, env):
        checks = run_smoke(LocalApiClient(url))
        assert {check.status for check in checks} == {"PASS"}
        with urlopen(url, timeout=2) as reply:
            assert reply.geturl() == url + "/demo"
            html = reply.read().decode("utf-8")
            assert 'data-runtime="api"' in html
        for asset in ("app.mjs", "client.mjs", "mock.mjs", "preparation.mjs"):
            with urlopen(url + "/demo/assets/" + asset, timeout=2) as reply:
                assert reply.headers.get_content_type() == "text/javascript"
                assert reply.read()
        result = subprocess.run([sys.executable, str(runtime / "scripts/check_readiness.py")],
                                env=env, capture_output=True, timeout=5)
        assert result.returncode == 0 and not result.stdout and not result.stderr
        # Runtime readiness reflects loss of its externally mounted DB.
        database.rename(tmp_path / "removed.sqlite3")
        result = subprocess.run([sys.executable, str(runtime / "scripts/check_readiness.py")],
                                env=env, capture_output=True, timeout=5)
        assert result.returncode == 1
    assert (tmp_path / "removed.sqlite3").read_bytes() == original


@pytest.mark.parametrize("value", ["0", "65536", "invalid", "1.5"])
def test_invalid_platform_port_is_rejected(value):
    import argparse
    with pytest.raises(argparse.ArgumentTypeError):
        port_number(value)


@pytest.mark.parametrize("url", ["http://example.test", "https://user:key@example.test", "https://example.test/demo",
                                  "https://example.test?key=x", "https://example.test:bad", "https://example.test/#x",
                                  "https://example.test/\\other", "https://example.test /", "https://"])
def test_deployment_check_rejects_unsafe_origins(url):
    with pytest.raises(ValueError):
        DeployedApiClient(url)


def test_deployment_client_keeps_https_and_disables_redirects_and_proxy():
    from urllib.request import ProxyHandler
    client = DeployedApiClient("https://service.example.test/", timeout=3)
    assert client.base_url == "https://service.example.test" and client.timeout == 3
    # ProxyHandler({}) is intentionally absent after build_opener processing;
    # no environment proxy should be added to an explicit deployment check.
    assert not any(isinstance(handler, ProxyHandler) and handler.proxies for handler in client.opener.handlers)
    assert next(handler for handler in client.opener.handlers if hasattr(handler, "redirect_request")).redirect_request(
        None, None, 302, "", {}, "https://other.example.test") is None
