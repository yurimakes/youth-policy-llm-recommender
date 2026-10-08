"""build_demo.py — 동일한 UI의 공개 체험용 정적 파일을 생성합니다."""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil


def build(destination: Path) -> None:
    """기존 파일을 삭제하지 않고 데모에 필요한 파일만 복사합니다."""
    source = Path(__file__).resolve().parents[1] / "demo"
    assets = destination / "demo" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    for name in ("style.css", "app.mjs", "client.mjs", "mock.mjs", "official-policies.json", "Pretendard-Regular.woff2",
                 "Pretendard-SemiBold.woff2", "Pretendard-ExtraBold.woff2", "Pretendard-OFL.txt"):
        shutil.copyfile(source / name, assets / name)
    html = (source / "index.html").read_text(encoding="utf-8").replace('data-runtime="api"', 'data-runtime="mock"')
    (destination / "index.html").write_text(html, encoding="utf-8")
    (destination / "demo" / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the labelled mock demo without API/DB dependencies")
    parser.add_argument("--output", required=True, type=Path)
    build(parser.parse_args().output)
