// UI 진행은 메모리에서만 유지하고 성공한 서버 응답으로만 교체한다.
export class IntakeSession {
  constructor(fetcher = globalThis.fetch.bind(globalThis)) {
    this.fetcher = fetcher;
    this.result = null;
    this.busy = false;
  }

  async request(path, body) {
    if (this.busy) throw new Error("진행 중인 요청이 끝난 뒤 다시 시도해 주세요.");
    this.busy = true;
    try {
      const response = await this.fetcher(path, {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body), cache: "no-store", credentials: "omit"
      });
      const payload = await response.json();
      if (!response.ok) {
        const messages = {
          503: "정책 데이터를 불러오지 못했어요. 데이터 준비 상태를 확인한 뒤 다시 시도해 주세요.",
          409: "현재 결과에서 진행할 수 없는 동작이에요. 다른 정책을 선택하거나 답변을 확인해 주세요.",
          422: "입력한 값과 진행 상태를 확인해 주세요. 이전 답변은 그대로 유지했어요."
        };
        throw new Error(messages[response.status] || "안내를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.");
      }
      if (payload.api_version !== "1" || !payload.state || !Array.isArray(payload.candidates)
          || typeof payload.notice !== "string" || !["start","interest","basic","detail","results","preparation"].includes(payload.state.stage)) {
        throw new Error("안내 응답을 확인할 수 없어요. 잠시 후 다시 시도해 주세요.");
      }
      this.result = payload;
      return payload;
    } finally {
      this.busy = false;
    }
  }

  start(mode) { return this.request("/api/v1/intake/start", {start_mode: mode}); }

  transition(action) {
    if (!this.result) throw new Error("먼저 상황이나 목표를 선택해 주세요.");
    return this.request("/api/v1/intake/transition", {state: this.result.state, action});
  }
}

export function safeSourceUrl(value) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value);
    return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password ? url.href : null;
  } catch { return null; }
}

export function formatVerifiedAt(value) {
  if (typeof value !== "string") return "확인 시점 미기록";
  // 기존 저장소의 timezone 없는 처리 시각은 UTC이다.
  const timestamp = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value) ? value : value + "Z";
  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? "확인 시점 미기록" : new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit"
  }).format(date);
}

export function viewForStage(stage) {
  return stage === "start" ? "start" : ["results", "preparation"].includes(stage) ? "results" : "question";
}
