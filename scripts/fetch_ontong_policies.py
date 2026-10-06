"""fetch_ontong_policies.py

온통청년 청년정책 API를 1회 호출해 원본 응답을 저장합니다.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPOSITORY_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from youth_policy.config import ConfigurationError, get_ontong_api_key
from youth_policy.ontong_client import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PAGE_NUM,
    DEFAULT_PAGE_SIZE,
    DEFAULT_PAGE_TYPE,
    DEFAULT_RTN_TYPE,
    fetch_ontong_policies,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch one page from the Ontong youth policy API.",
    )
    parser.add_argument("--page-num", type=int, default=DEFAULT_PAGE_NUM)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument("--page-type", type=int, default=DEFAULT_PAGE_TYPE)
    parser.add_argument(
        "--rtn-type",
        choices=("json", "xml"),
        default=DEFAULT_RTN_TYPE,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout", type=float, default=10.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        api_key = get_ontong_api_key()
        result = fetch_ontong_policies(
            api_key=api_key,
            output_dir=args.output_dir,
            page_num=args.page_num,
            page_size=args.page_size,
            page_type=args.page_type,
            rtn_type=args.rtn_type,
            timeout=args.timeout,
        )
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Ontong API fetch failed: {exc}", file=sys.stderr)
        return 1

    print("HTTP success: yes")
    print(f"Response format: {result.response_format}")
    print(f"Raw response path: {result.raw_path}")
    print(f"Metadata path: {result.metadata_path}")
    print(f"Response size bytes: {result.response_size_bytes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
