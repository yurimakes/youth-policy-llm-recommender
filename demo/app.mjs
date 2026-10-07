import {IntakeSession, safeSourceUrl, formatVerifiedAt, viewForStage} from "./client.mjs";

const session = new IntakeSession();
const $ = id => document.getElementById(id);
const factLabels = {age: "만 나이", region_code: "거주 지역", employment_status: "취업 상태"};
const checkLabels = {age: "연령", region_code: "거주 지역", employment_status: "취업 상태", application: "신청 기간", income: "소득", education: "학력", eligibility: "추가 조건"};
const optionCache = new Map();
let retryAction = null;
let draftCard = null;
let cardQuestion = null;
let disabledBefore = new Map();

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function actionButton(text, action, style = "primary") {
  const button = el("button", style, text);
  button.type = "button";
  button.addEventListener("click", () => transition(action));
  return button;
}

function setBusy(busy) {
  $("loading").hidden = !busy;
  $("main").setAttribute("aria-busy", String(busy));
  if (busy) {
    disabledBefore = new Map();
    document.querySelectorAll("button,input,select").forEach(node => {
      disabledBefore.set(node, node.disabled);
      node.disabled = true;
    });
  } else {
    disabledBefore.forEach((disabled, node) => { if (node.isConnected) node.disabled = disabled; });
    disabledBefore.clear();
  }
}

async function perform(operation, {restart = false} = {}) {
  if (session.busy) return false;
  $("error").hidden = true;
  $("edit-error").hidden = true;
  setBusy(true);
  let succeeded = false;
  try {
    await operation();
    setBusy(false);
    if (restart) optionCache.clear();
    render();
    retryAction = null;
    succeeded = true;
  } catch (error) {
    retryAction = () => perform(operation, {restart});
    $("error-text").textContent = error.message;
    // Network and malformed-response errors never echo a submitted value.
    if (error instanceof TypeError || error instanceof SyntaxError) {
      $("error-text").textContent = "안내를 불러오지 못했어요. 서버 연결 상태를 확인한 뒤 다시 시도해 주세요.";
    }
    $("error").hidden = false;
    if ($("edit-dialog").open) {
      $("edit-error").textContent = $("error-text").textContent;
      $("edit-error").hidden = false;
    } else $("error").scrollIntoView({block: "nearest"});
  } finally { setBusy(false); }
  if (succeeded) {
    const view = viewForStage(session.result.state.stage);
    $(`${view === "results" ? "results" : view}-heading`).focus();
  }
  return succeeded;
}

const transition = action => perform(() => session.transition(action));
const start = mode => perform(() => session.start(mode), {restart: true});

function cards(question, container, name) {
  container.replaceChildren();
  draftCard = null;
  cardQuestion = question;
  const icons = {school: "🎓", working: "💼", resting: "☕", unknown: "?",
                 employment: "💼", housing: "🏠", learning: "📚",
                 living_cost: "₩", low_burden: "🌱", counseling: "💬"};
  question.options.forEach(option => {
    const card = el("label", "choice-card");
    const radio = el("input");
    radio.type = "radio";
    radio.name = name;
    radio.value = option.value;
    radio.setAttribute("aria-label", option.label);
    const icon = el("span", "choice-number", icons[option.value] || "·");
    icon.setAttribute("aria-hidden", "true");
    const check = el("span", "radio-check", "✓");
    check.setAttribute("aria-hidden", "true");
    card.append(radio, icon, el("span", "choice-label", option.label), check);
    radio.addEventListener("change", () => {
      draftCard = option.value;
      const button = $(name === "opening-card" ? "opening-next" : "submit-answer");
      button.disabled = false;
    });
    container.append(card);
  });
}

function makeInput(key, options, value, container, prefix) {
  container.replaceChildren();
  const label = el("label", "", factLabels[key] || "답변");
  label.htmlFor = prefix + "-value";
  container.append(label);
  let input;
  if (key === "age") {
    input = el("input");
    input.type = "number"; input.min = "0"; input.max = "120"; input.step = "1";
    input.inputMode = "numeric";
    input.placeholder = "만 나이를 입력해 주세요";
    input.value = value ?? "";
  } else {
    input = el("select");
    const blank = el("option", "", "선택해 주세요"); blank.value = "";
    input.append(blank);
    options.forEach(choice => {
      const option = el("option", "", choice.label); option.value = choice.value;
      input.append(option);
    });
    if (key === "region_code") {
      const manual = el("option", "", "목록에 없는 지역 · 코드 직접 입력"); manual.value = "__manual__";
      input.append(manual);
    }
    input.value = value ?? "";
    if (value && !options.some(option => option.value === value) && key === "region_code") input.value = "__manual__";
  }
  input.id = prefix + "-value";
  input.required = true;
  container.append(input);
  if (key === "region_code") {
    const manualBox = el("div", "manual-region");
    const manualLabel = el("label", "", "거주 지역 5자리 코드");
    const manual = el("input"); manual.id = prefix + "-manual";
    manualLabel.htmlFor = manual.id; manual.type = "text"; manual.inputMode = "numeric";
    manual.pattern = "[0-9]{5}"; manual.maxLength = 5; manual.placeholder = "5자리 코드";
    manual.value = value && input.value === "__manual__" ? value : "";
    manualBox.append(manualLabel, manual, el("p", "input-hint", "목록은 전체 지역을 포함하지 않아요. 코드를 모르면 건너뛰어도 괜찮아요."));
    container.append(manualBox);
    const toggle = () => { manualBox.hidden = input.value !== "__manual__"; manual.required = !manualBox.hidden; manual.disabled = manualBox.hidden; };
    input.addEventListener("change", toggle); toggle();
  }
}

function inputValue(prefix, key) {
  const input = $(prefix + "-value");
  return key === "age" ? Number(input.value) : input.value === "__manual__" ? $(prefix + "-manual").value : input.value;
}

function renderQuestion(result) {
  const question = result.next_question;
  const detail = result.state.stage === "detail";
  $("question-tag").textContent = detail ? "선택한 정책, 조금 더 확인하기" : "필요한 정보만 하나씩";
  $("pause-detail").hidden = !detail;
  $("show-results").hidden = !result.can_show_results;
  $("answer-form").hidden = !question;
  $("question-options").hidden = true;
  if (!question) {
    $("question-heading").textContent = "지금 정보로 살펴볼까요?";
    $("question-purpose").textContent = "현재 후보에 필요한 질문을 확인했어요. 모르는 조건은 결과에서 확인할 수 있어요.";
    $("show-results").textContent = "정책 결과 보기 →";
    return;
  }
  $("question-heading").textContent = question.prompt;
  $("question-purpose").textContent = question.purpose;
  $("show-results").textContent = "지금 정보로 결과 보기 →";
  $("skip-answer").hidden = !question.allow_skip;
  $("submit-answer").disabled = question.input_type === "card";
  if (question.input_type === "card") {
    $("question-input").replaceChildren();
    cards(question, $("question-input"), "question-card");
  } else makeInput(question.key, question.options, result.state.profile[question.key], $("question-input"), "answer");
}

function policyCard(candidate, result) {
  const selected = result.state.interested_policy_id === candidate.policy_id;
  const article = el("article", "policy-card" + (selected ? " selected" : ""));
  const top = el("div", "policy-top");
  top.append(el("h3", "", candidate.policy_name), el("span", "badge " + candidate.status,
    candidate.status === "confirmed" ? "개별 조건 확인됨" : candidate.status_label));
  article.append(top);
  if (candidate.summary || candidate.benefit_text) article.append(el("p", "policy-summary", candidate.summary || candidate.benefit_text));
  const details = el("details", "conditions");
  details.append(el("summary", "", "조건별 확인사항 보기"));
  const list = el("ul", "check-list");
  candidate.checks.forEach(check => {
    const item = el("li");
    item.append(el("span", "", checkLabels[check.field] || "확인 항목"), el("span", "check-state", check.status_label), el("span", "reason", check.reason));
    list.append(item);
  });
  details.append(list); article.append(details);
  const actions = el("ul", "next-actions");
  candidate.next_actions.forEach(text => actions.append(el("li", "", text)));
  article.append(actions);
  const footer = el("div", "policy-footer");
  const source = el("div", "source", candidate.source_name + " · 데이터 기준 " + formatVerifiedAt(candidate.last_verified_at));
  const url = safeSourceUrl(candidate.source_url);
  if (url) {
    const link = el("a", "", "공식 공고 확인하기 ↗");
    link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer";
    source.append(link);
  } else source.append(el("p", "", "공식 공고 링크를 제공기관에서 확인해 주세요."));
  footer.append(source);
  if (result.state.stage === "results") footer.append(actionButton(selected ? "선택한 정책" : "이 정책 확인하기",
    {type: "select_policy", policy_id: candidate.policy_id}, "secondary"));
  article.append(footer);
  return article;
}

function renderResults(result) {
  const preparation = result.state.stage === "preparation";
  $("results-heading").textContent = preparation ? "다음 확인을 준비해 볼까요?" : result.candidates.length ? "확인해 볼 정책을 찾았어요." : "다른 지원도 살펴볼까요?";
  $("results-description").textContent = "입력한 정보와 정책 조건을 비교한 후보예요. 개인별 적합도 순위는 아니에요.";
  $("notice-text").textContent = result.notice;
  $("candidate-count").textContent = result.candidates.length + "개";
  $("empty-results").hidden = result.candidates.length > 0;
  const facts = Object.keys(factLabels).filter(key => result.state.answered.includes(key) || result.state.skipped.includes(key));
  $("edit-answers").hidden = facts.length === 0;
  $("profile-summary").replaceChildren();
  facts.forEach(key => {
    const value = result.state.profile[key];
    const option = (optionCache.get(key) || []).find(choice => choice.value === value);
    const label = value === null ? "모름 · 건너뛰기" : key === "age" ? `${value}세` : option?.label || value;
    $("profile-summary").append(el("span", "profile-chip", `${factLabels[key]} · ${label}`));
  });
  $("candidate-list").replaceChildren(...result.candidates.map(candidate => policyCard(candidate, result)));
  const selected = result.candidates.find(candidate => candidate.policy_id === result.state.interested_policy_id);
  const panel = $("detail-panel"); panel.replaceChildren();
  panel.hidden = preparation || !result.state.interested_policy_id;
  if (!panel.hidden) {
    panel.append(el("h2", "", selected?.policy_name || "선택한 정책이 현재 후보에서 제외됐어요."));
    if (result.selected_policy_excluded) panel.append(el("p", "", "수정한 답변 또는 현재 정책 조건에 따라 후보가 바뀌었어요. 아래에서 다른 정책을 확인해 주세요."));
    else if (result.state.detail_paused) {
      panel.append(el("p", "", "기존 답변은 유지했어요. 준비되면 상세 확인을 이어갈 수 있어요."), actionButton("상세 확인 이어가기", {type: "resume_detail"}));
    } else if (result.detail_offer_available) {
      panel.append(el("p", "", "관심 있는 정책의 조건을 조금 더 확인할까요? 추가 질문 없이 기본 안내를 유지해도 괜찮아요."));
      const controls = el("div", "actions");
      controls.append(actionButton("추가 조건 확인하기", {type: "choose_detail", accept: true}), actionButton("지금 정보로 볼게요", {type: "choose_detail", accept: false}, "secondary"));
      panel.append(controls);
    } else panel.append(el("p", "", result.state.detail_choice === false ? "추가 질문 없이 기본 안내를 유지하고 있어요." : "현재 답변으로 확인할 수 있는 조건을 살펴봤어요. 남은 항목은 공식 공고에서 확인해 주세요."));
    if (selected) panel.append(actionButton("다음 확인할 항목 보기", {type: "prepare"}, "text-button"));
  }
  $("preparation-panel").hidden = !preparation;
  $("preparation-actions").replaceChildren();
  if (preparation) {
    const items = selected ? selected.next_actions : ["관심 있는 정책의 공식 공고에서 최종 자격과 준비 절차를 확인해 주세요."];
    items.forEach(text => $("preparation-actions").append(el("li", "", text)));
  }
}

function render() {
  const result = session.result;
  const question = result.next_question;
  if (question && question.input_type !== "card") optionCache.set(question.key, question.options);
  const view = viewForStage(result.state.stage);
  ["start", "question", "results"].forEach(name => { $(name + "-view").hidden = name !== view; });
  document.querySelectorAll("[data-step]").forEach(node => {
    if (node.dataset.step === view) node.setAttribute("aria-current", "step"); else node.removeAttribute("aria-current");
  });
  $("situation-mode").setAttribute("aria-pressed", String(result.state.start_mode === "situation"));
  $("goal-mode").setAttribute("aria-pressed", String(result.state.start_mode === "goal"));
  if (view === "start") {
    $("opening-prompt").textContent = question.prompt;
    $("start-heading").textContent = question.prompt;
    cards(question, $("opening-options"), "opening-card");
    $("opening-next").disabled = true;
  } else if (view === "question") renderQuestion(result);
  else renderResults(result);
}

function renderEdit() {
  const key = $("edit-key").value;
  $("edit-unknown").checked = session.result.state.profile[key] === null;
  makeInput(key, optionCache.get(key) || [], session.result.state.profile[key], $("edit-input"), "edit");
  toggleUnknown();
}

function toggleUnknown() {
  $("edit-input").querySelectorAll("input,select").forEach(node => {
    const manualHidden = node.id === "edit-manual" && $("edit-value").value !== "__manual__";
    node.disabled = $("edit-unknown").checked || manualHidden;
  });
}

$("situation-mode").addEventListener("click", () => start("situation"));
$("goal-mode").addEventListener("click", () => start("goal"));
$("restart").addEventListener("click", () => { if (window.confirm("입력한 답변을 지우고 처음부터 시작할까요?")) start("situation"); });
$("retry").addEventListener("click", () => retryAction?.());
$("opening-next").addEventListener("click", () => { if (draftCard !== null) transition({type: "choose_card", key: cardQuestion.key, value: draftCard}); });
$("opening-skip").addEventListener("click", () => { if (session.result) transition({type: "choose_card", key: session.result.next_question.key, value: null}); });
$("answer-form").addEventListener("submit", event => {
  event.preventDefault();
  const question = session.result.next_question;
  if (question.input_type === "card" && draftCard === null) return;
  transition({type: question.input_type === "card" ? "choose_card" : "answer_fact", key: question.key,
              value: question.input_type === "card" ? draftCard : inputValue("answer", question.key)});
});
$("skip-answer").addEventListener("click", () => {
  const question = session.result.next_question;
  transition({type: question.input_type === "card" ? "choose_card" : "answer_fact", key: question.key, value: null});
});
$("show-results").addEventListener("click", () => transition({type: "show_results"}));
$("pause-detail").addEventListener("click", () => transition({type: "pause_detail"}));
$("back-results").addEventListener("click", () => transition({type: "show_results"}));
$("edit-answers").addEventListener("click", () => {
  $("edit-error").hidden = true;
  $("edit-key").replaceChildren();
  Object.keys(factLabels).filter(key => session.result.state.answered.includes(key) || session.result.state.skipped.includes(key)).forEach(key => {
    const option = el("option", "", factLabels[key]); option.value = key; $("edit-key").append(option);
  });
  renderEdit(); $("edit-dialog").showModal();
});
$("edit-key").addEventListener("change", renderEdit);
$("edit-unknown").addEventListener("change", toggleUnknown);
$("close-edit").addEventListener("click", () => $("edit-dialog").close());
$("edit-form").addEventListener("submit", async event => {
  event.preventDefault();
  const key = $("edit-key").value;
  const success = await transition({type: "answer_fact", key, value: $("edit-unknown").checked ? null : inputValue("edit", key)});
  if (success) $("edit-dialog").close();
});

start("situation");
