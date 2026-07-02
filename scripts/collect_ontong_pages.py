"""collect_ontong_pages.py

온통청년 API 여러 페이지를 수집해 SQLite DB에 적재하는 CLI입니다.
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

from career_catch.collection import (
    DEFAULT_MAX_PAGES,
    DEFAULT_START_PAGE,
    collect_ontong_policy_pages,
)
from career_catch.config import ConfigurationError, get_ontong_api_key
from career_catch.ontong_client import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEOUT_SECONDS,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect Ontong youth policy API pages into SQLite.",
    )
    parser.add_argument(
        "--db",
        required=True,
        type=Path,
        help="SQLite database path to create or update.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--start-page", type=int, default=DEFAULT_START_PAGE)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        api_key = get_ontong_api_key()
        result = collect_ontong_policy_pages(
            api_key=api_key,
            db_path=args.db,
            output_dir=args.output_dir,
            start_page=args.start_page,
            page_size=args.page_size,
            max_pages=args.max_pages,
            timeout=args.timeout,
        )
    except ConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Ontong page collection failed: {exc}", file=sys.stderr)
        return 1

    print(f"fetched_pages={','.join(str(page) for page in result.fetched_pages)}")
    print(f"fetched_policies={result.fetched_policies}")
    print(f"stored_policies={result.stored_policies}")
    print(f"total_available={result.total_available}")
    print(f"db={result.db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
