import test from "node:test";
import assert from "node:assert/strict";
import {IntakeSession, safeSourceUrl, formatVerifiedAt, viewForStage, basicQuestionProgress} from "../demo/client.mjs";
import './test_preparation.mjs';

test('basic progress follows completed facts instead of the question key or card history',()=>{
 assert.equal(basicQuestionProgress({answered:['situation','interest'],skipped:[]}),50);
 for(const key of ['age','region_code']){
  assert.equal(basicQuestionProgress({answered:[key],skipped:[]}),100);
  assert.equal(basicQuestionProgress({answered:[],skipped:[key]}),100);
 }
});

test('evidence request is explicit and never replaces the intake state',async()=>{
 const result=payload('results');result.candidates=[{policy_id:'TEST'}];
 const evidence={api_version:'1',policy_id:'TEST',mode:'source_only',ai_available:true,notice:'공고 확인',checks:[],items:[]};
 let body;
 const session=new IntakeSession(async(path,options)=>{assert.equal(path,'/api/v1/intake/explanation');body=JSON.parse(options.body);return response(evidence);});
 session.result=result;
 assert.equal(await session.explain('TEST'),evidence);
 assert.equal(body.use_ai,false);assert.equal(body.focus,'overview');assert.deepEqual(body.state,result.state);
 assert.equal(session.result,result);assert.equal(session.busy,false);
 await session.explain('TEST',{useAI:true,focus:'preparation'});assert.equal(body.use_ai,true);
});

test('failed and mismatched evidence responses preserve answers and basket input',async()=>{
 for(const [body,status] of [[{},503],[{api_version:'1',policy_id:'OTHER',mode:'source_only',items:[]},200]]){
  const result=payload('results');result.candidates=[{policy_id:'TEST'}];
  const session=new IntakeSession(async()=>response(body,status));session.result=result;
  await assert.rejects(()=>session.explain('TEST'));assert.equal(session.result,result);assert.equal(session.busy,false);
 }
});

test('unknown policy explanation is rejected without a request',async()=>{
 let calls=0;const session=new IntakeSession(async()=>{calls++;});session.result=payload('results');
 await assert.rejects(()=>session.explain('OTHER'));assert.equal(calls,0);
});

const payload = (stage = "start") => ({api_version: "1", state: {stage, revision: 0}, candidates: [], notice: "공식 공고 확인"});
const response = (body, status = 200) => ({ok: status === 200, status, json: async () => body});

test('timeout aborts a hanging request and retry ignores its late response', async () => {
  let finish, signal, calls = 0;
  const previous = payload('basic'), retried = payload('results');
  const session = new IntakeSession((path, options) => {
    calls++;
    if (calls === 1) { signal = options.signal; return new Promise(resolve => { finish = resolve; }); }
    return Promise.resolve(response(retried));
  }, {timeoutMs: 20});
  session.result = previous;
  await assert.rejects(session.transition({type:'show_results'}), /이전 답변은 유지/);
  assert.equal(signal.aborted, true); assert.equal(session.busy, false);
  assert.equal(session.result, previous); assert.equal(calls, 1);
  await session.transition({type:'show_results'});
  finish(response(payload('start')));
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(session.result, retried); assert.equal(calls, 2);
});

test('evidence JSON decoding is bounded and preserves the prior state', async () => {
  const previous = payload('results'); previous.candidates = [{policy_id:'TEST'}];
  let signal;
  const session = new IntakeSession(async (_, options) => {
    signal = options.signal; return {ok:true, json:() => new Promise(() => {})};
  }, {timeoutMs:20});
  session.result = previous;
  await assert.rejects(session.explain('TEST', {useAI:true}), /연결이 오래/);
  assert.equal(signal.aborted, true); assert.equal(session.busy, false); assert.equal(session.result, previous);
});

test('successful request clears its deadline without aborting the transport', async () => {
  let signal;
  const session = new IntakeSession(async (_, options) => {signal = options.signal; return response(payload());}, {timeoutMs:20});
  await session.start('situation');
  await new Promise(resolve => setTimeout(resolve, 40));
  assert.equal(signal.aborted, false); assert.equal(session.busy, false);
});

test('invalid request deadlines are rejected', () => {
  for (const timeoutMs of [0, -1, NaN, Infinity]) assert.throws(() => new IntakeSession(async()=>{}, {timeoutMs}));
});

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
