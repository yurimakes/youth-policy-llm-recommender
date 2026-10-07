"""preview_intake.py

기존 SQLite 정책으로 간편·상세 확인 흐름을 로컬 터미널에서 점검합니다.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from youth_policy.conditions import EMPLOYMENT_VALUES, STATUS_LABELS
from youth_policy.intake import (
    CARD_OPTIONS, IntakeState, answer_fact, choose_card, choose_detail, pause_detail,
    resume_detail, select_policy, show_results, start_intake,
)
from youth_policy.intake_service import build_guidance, detail_is_useful, next_question
from youth_policy.models import PolicyRecord
from youth_policy.sqlite_store import list_policies


def load_read_only(database: Path) -> tuple[PolicyRecord, ...]:
    """기존 DB를 읽기 전용으로 열어 새 파일 생성과 사용자 답변 저장을 막습니다."""
    if not database.is_file():
        raise ValueError("정책 DB가 없습니다. 기존 collect_ontong_pages.py로 먼저 준비하세요.")
    connection = sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        return tuple(list_policies(connection))
    finally:
        connection.close()


def _pick_card(state: IntakeState, key: str) -> IntakeState:
    options = CARD_OPTIONS[key]
    for i, (_, label) in enumerate(options, 1):
        print(f"{i}. {label}")
    while True:
        raw = input("번호 선택 (Enter: 건너뛰기): ").strip()
        if not raw:
            return choose_card(state, key, None)
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return choose_card(state, key, options[int(raw) - 1][0])
        print("표시된 번호를 선택하세요.")


def _questions(state: IntakeState, policies: tuple[PolicyRecord, ...]) -> IntakeState:
    while (question := next_question(state, policies, reference_date=date.today())) is not None:
        print(question.prompt)
        print(question.purpose)
        if question.key == "region_code":
            print("이 개발용 CLI에서는 5자리 거주 지역 코드를 입력합니다. 예: 11680")
        elif question.key == "employment_status":
            print(" / ".join(sorted(EMPLOYMENT_VALUES)))
        raw = input("답변 (Enter: 모름·건너뛰기, /pause: 상세 질문 중단): ").strip()
        if raw == "/pause" and state.stage.value == "detail":
            return pause_detail(state)
        try:
            value = int(raw) if raw and question.key == "age" else (raw or None)
            state = answer_fact(state, question.key, value)
        except ValueError:
            print("입력 형식을 확인하거나 Enter로 건너뛰세요.")
    return show_results(state)


def preview(policies: tuple[PolicyRecord, ...], start_mode: str) -> None:
    print("지원장바구니 — 진행 로직 개발용 CLI (웹 화면 아님)")
    print("답변은 메모리에서만 사용합니다. 외부 AI 호출과 신청 자격 확정을 하지 않습니다.")
    state = _pick_card(start_intake(start_mode), start_mode)
    if start_mode == "situation":
        state = _pick_card(state, "interest")
    state = _questions(state, policies)
    results = build_guidance(policies, state, reference_date=date.today())
    if not results:
        print("현재 데이터와 확인된 조건에서 안내할 후보가 없습니다. 최신 공식 공고를 확인하세요.")
        return
    print("현재 조건에서 추가 확인할 후보입니다. 관심에 따른 추천 순위는 아직 적용하지 않습니다.")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.policy_name} — {STATUS_LABELS[result.assessment.status]}")
    raw = input("관심 정책 번호 (Enter: 현재 안내로 종료): ").strip()
    if not raw:
        return
    if not raw.isdigit() or not 1 <= int(raw) <= len(results):
        print("표시된 후보 번호가 아니므로 종료합니다.")
        return
    selected = results[int(raw) - 1]
    state = select_policy(state, selected.policy_id, tuple(r.policy_id for r in results))
    useful = detail_is_useful(state, policies, reference_date=date.today())
    if useful:
        accept = input("필요한 조건을 더 자세히 확인할까요? (y: 확인 / Enter: 현재 안내): ").strip().lower() == "y"
        state = choose_detail(state, accept, needs_information=True)
        if accept:
            state = _questions(state, policies)
            if state.detail_paused and input("중단한 질문으로 돌아갈까요? (y / Enter): ").strip().lower() == "y":
                state = _questions(resume_detail(state), policies)
    refreshed = build_guidance(policies, state, reference_date=date.today())
    selected_result = next((r for r in refreshed if r.policy_id == selected.policy_id), None)
    if selected_result is None:
        print("추가 답변으로 선택한 정책의 명확한 불일치가 확인됐습니다. 다른 공식 지원을 확인하세요.")
        return
    for check in selected_result.assessment.checks:
        print(f"- {STATUS_LABELS[check.status]}: {check.reason}")
    for action in selected_result.next_actions:
        print(f"- 다음 행동: {action}")
    print(f"공식 링크: {selected_result.source_url or '확인 필요'}")
    print(f"데이터 확인 시각: {selected_result.last_verified_at.isoformat()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="지원장바구니 진행 로직 로컬 점검")
    parser.add_argument("--db", type=Path, default=Path("data/processed/policies.sqlite3"))
    parser.add_argument("--start", choices=("situation", "goal"), default="situation")
    args = parser.parse_args()
    try:
        preview(load_read_only(args.db), args.start)
    except (ValueError, sqlite3.Error) as exc:
        parser.exit(1, f"정책 데이터 확인 실패: {exc}\n")
    except (EOFError, KeyboardInterrupt):
        print("\n로컬 점검을 종료했습니다. 답변을 저장하지 않았습니다.")


if __name__ == "__main__":
    main()
