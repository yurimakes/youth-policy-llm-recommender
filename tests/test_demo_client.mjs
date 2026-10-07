import test from "node:test";
import assert from "node:assert/strict";
import {IntakeSession, safeSourceUrl, formatVerifiedAt, viewForStage} from "../demo/client.mjs";

const payload = (stage = "start") => ({api_version: "1", state: {stage, revision: 0}, candidates: [], notice: "공식 공고 확인"});
const response = (body, status = 200) => ({ok: status === 200, status, json: async () => body});

test("next POST sends the complete prior state and uses relative same-origin routes", async () => {
  const requests = [];
  const initial = payload();
  const updated = payload("basic");
  const session = new IntakeSession(async (path, options) => {
    requests.push({path, options});
    return response(requests.length === 1 ? initial : updated);
  });
  await session.start("situation");
  await session.transition({type: "choose_card", key: "situation", value: "resting"});
  assert.equal(requests[1].path, "/api/v1/intake/transition");
  assert.deepEqual(JSON.parse(requests[1].options.body).state, initial.state);
  assert.equal(requests[1].options.cache, "no-store");
  assert.equal(requests[1].options.credentials, "omit");
  assert.equal(session.result, updated);
});

test("server rejection preserves the latest successful state without echoing the error body", async () => {
  const initial = payload();
  let calls = 0;
  const session = new IntakeSession(async () => response(++calls === 1 ? initial : {error: {message: "PRIVATE-MARKER"}}, calls === 1 ? 200 : 422));
  await session.start("situation");
  await assert.rejects(session.transition({type: "answer_fact", key: "age", value: true}), error => {
    assert.ok(!error.message.includes("PRIVATE-MARKER")); return true;
  });
  assert.equal(session.result, initial);
  assert.equal(session.busy, false);
});

test("concurrent transitions are rejected before a second request is sent", async () => {
  let complete;
  let calls = 0;
  const session = new IntakeSession(() => { calls++; return new Promise(resolve => { complete = resolve; }); });
  const first = session.start("situation");
  await assert.rejects(session.start("goal"));
  assert.equal(calls, 1);
  complete(response(payload()));
  await first;
  assert.equal(session.busy, false);
});

test("network and malformed success responses leave the old result available for retry", async () => {
  const initial = payload();
  let calls = 0;
  const session = new IntakeSession(async () => {
    calls++;
    if (calls === 1) return response(initial);
    if (calls === 2) throw new TypeError("network");
    return response({api_version: "wrong"});
  });
  await session.start("situation");
  await assert.rejects(session.transition({type: "show_results"}));
  await assert.rejects(session.transition({type: "show_results"}));
  assert.equal(session.result, initial);
  assert.equal(session.busy, false);
});

test("official links reject executable schemes and embedded credentials", () => {
  for (const url of [null, "javascript:alert(1)", "data:text/html,x", "file:///private", "https://user:secret@example.test/"]) assert.equal(safeSourceUrl(url), null);
  assert.equal(safeSourceUrl("https://example.test/official"), "https://example.test/official");
});

test("stored naive UTC processing times display the Korea calendar date", () => {
  assert.equal(formatVerifiedAt("2026-10-07T16:30:00"), formatVerifiedAt("2026-10-08T01:30:00+09:00"));
  assert.equal(formatVerifiedAt("invalid"), "확인 시점 미기록");
  assert.equal(formatVerifiedAt(null), "확인 시점 미기록");
});

test("all API stages map into the three demo screens", () => {
  assert.equal(viewForStage("start"), "start");
  for (const stage of ["interest", "basic", "detail"]) assert.equal(viewForStage(stage), "question");
  for (const stage of ["results", "preparation"]) assert.equal(viewForStage(stage), "results");
});
