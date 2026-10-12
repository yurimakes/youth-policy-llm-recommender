// UI 진행은 메모리에서만 유지하고 성공한 서버 응답으로만 교체한다.
export class IntakeSession {
  constructor(fetcher = globalThis.fetch.bind(globalThis), {timeoutMs = 10000} = {}) {
    if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) throw new Error('요청 시간 제한을 확인해 주세요.');
    this.fetcher = fetcher;
    this.timeoutMs = timeoutMs;
    this.result = null;
    this.busy = false;
  }

  async post(path, body) {
    const controller = new AbortController();
    let timer;
    const deadline = new Promise((_, reject) => {
      timer = setTimeout(() => {
        controller.abort();
        reject(new Error('연결이 오래 걸리고 있어요. 이전 답변은 유지했어요. 잠시 후 다시 시도해 주세요.'));
      }, this.timeoutMs);
    });
    try {
      // Include JSON body decoding in the deadline. Ignore a late result even if
      // an injected transport does not honor AbortSignal.
      return await Promise.race([deadline, (async () => {
        const response = await this.fetcher(path, {
          method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(body), cache: 'no-store', credentials: 'omit', signal: controller.signal
        });
        return {response, payload: await response.json()};
      })()]);
    } finally { clearTimeout(timer); }
  }

  async request(path, body) {
    if (this.busy) throw new Error("진행 중인 요청이 끝난 뒤 다시 시도해 주세요.");
    this.busy = true;
    try {
      const {response, payload} = await this.post(path, body);
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

  async explain(policyId, {focus = 'overview', useAI = false} = {}) {
    if (this.busy) throw new Error('진행 중인 요청이 끝난 뒤 다시 시도해 주세요.');
    if (!this.result || !this.result.candidates.some(c => c.policy_id === policyId)) {
      throw new Error('현재 결과의 지원을 선택해 주세요.');
    }
    this.busy = true;
    try {
      const {response, payload} = await this.post('/api/v1/intake/explanation', {
        state: this.result.state, policy_id: policyId, focus, use_ai: useAI
      });
      if (!response.ok) throw new Error(response.status === 409
        ? '지원 조건이 달라졌을 수 있어요. 답변과 후보를 다시 확인해 주세요.'
        : '근거를 불러오지 못했어요. 기존 답변은 유지했어요.');
      if (payload.api_version !== '1' || payload.policy_id !== policyId
          || !['source_only','ai_selected'].includes(payload.mode)
          || typeof payload.ai_available !== 'boolean' || typeof payload.notice !== 'string'
          || !Array.isArray(payload.checks) || !Array.isArray(payload.items) || payload.items.length > 3
          || payload.items.some(item => typeof item.evidence_id !== 'string'
            || typeof item.label !== 'string' || typeof item.excerpt !== 'string'
            || typeof item.truncated !== 'boolean')) {
        throw new Error('근거 응답을 확인할 수 없어요. 기존 답변은 유지했어요.');
      }
      return payload;
    } finally { this.busy = false; }
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

export function basicQuestionProgress(state) {
  const completed = new Set([...(state.answered || []), ...(state.skipped || [])]
    .filter(key => ['age', 'region_code'].includes(key)));
  return Math.min(100, (completed.size + 1) * 50);
}
