import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DemoSession,DEMO_NOTICE} from '../demo/mock.mjs';
import {safeSourceUrl} from '../demo/client.mjs';

async function basic({skip=false,mode='situation'}={}){
 const s=new DemoSession();await s.start(mode);
 await s.transition({type:'choose_card',key:mode,value:skip?'unknown':mode==='goal'?'employment':'resting'});
 if(mode==='situation')await s.transition({type:'choose_card',key:'interest',value:skip?null:'living_cost'});
 await s.transition({type:'answer_fact',key:'region_code',value:skip?null:'11000'});
 await s.transition({type:'answer_fact',key:'age',value:skip?null:24});
 await s.transition({type:'show_results'});return s;
}
test('situation and interest never become residence, age or employment facts',async()=>{
 const s=new DemoSession();await s.start();
 await s.transition({type:'choose_card',key:'situation',value:'resting'});
 await s.transition({type:'choose_card',key:'interest',value:'living_cost'});
 assert.deepEqual(s.result.state.profile,{age:null,region_code:null,employment_status:null});
 assert.equal(s.result.next_question.key,'region_code');
 await s.transition({type:'answer_fact',key:'region_code',value:'11000'});
 assert.equal(s.result.next_question.key,'age');
 await s.transition({type:'answer_fact',key:'age',value:24});
 await s.transition({type:'show_results'});
 assert.ok(s.result.candidates.length>0);
 assert.equal(s.result.state.profile.employment_status,null);
 assert.ok(s.result.candidates.every(p=>p.status==='check_required'&&p.source_url===null));
 assert.equal(s.result.notice,DEMO_NOTICE);
});
test('unknown and skipped answers keep candidates and missing-input conditions',async()=>{
 const s=await basic({skip:true});
 assert.ok(s.result.candidates.length>0);
 assert.ok(s.result.state.skipped.includes('age'));
 assert.ok(s.result.candidates.every(p=>p.checks.some(c=>c.field==='age'&&c.status==='input_missing')));
 assert.ok(s.result.candidates.every(p=>p.checks.some(c=>c.status==='check_required')));
});
test('detail decline keeps basic candidates and next official checking actions',async()=>{
 const s=await basic(),before=s.result.candidates;
 await s.transition({type:'select_policy',policy_id:'DEMO-LIVING'});
 assert.equal(s.result.detail_offer_available,true);
 await s.transition({type:'choose_detail',accept:false});
 assert.equal(s.result.state.stage,'results');
 assert.deepEqual(s.result.candidates,before);
 assert.ok(s.result.candidates.every(p=>p.next_actions.length>0));
});
test('detail pause/resume reuses answers; explicit employment mismatch excludes candidates',async()=>{
 const s=await basic();
 await s.transition({type:'select_policy',policy_id:'DEMO-LIVING'});
 await s.transition({type:'choose_detail',accept:true});
 assert.equal(s.result.next_question.key,'household');
 await s.transition({type:'answer_demo',key:'household',value:'alone'});
 await s.transition({type:'pause_detail'});
 assert.equal(s.result.state.detail_paused,true);
 await s.transition({type:'resume_detail'});
 assert.equal(s.result.next_question.key,'employment_status');
 await s.transition({type:'answer_fact',key:'employment_status',value:'미취업자'});
 await s.transition({type:'answer_demo',key:'available_time',value:'weekend'});
 await s.transition({type:'show_results'});
 assert.equal(s.result.state.profile.age,24);
 await s.transition({type:'answer_fact',key:'employment_status',value:'중소기업 재직자'});
 assert.equal(s.result.selected_policy_excluded,true);
 assert.ok(!s.result.candidates.some(p=>p.policy_id==='DEMO-LIVING'||p.policy_id==='DEMO-JOB'));
 assert.ok(s.result.candidates.some(p=>p.policy_id==='DEMO-WORKER'));
 await s.transition({type:'answer_fact',key:'employment_status',value:null});
 assert.ok(s.result.candidates.some(p=>p.policy_id==='DEMO-LIVING'));
 assert.ok(s.result.state.skipped.includes('employment_status'));
});
test('age correction excludes known mismatches and unknown correction restores uncertainty',async()=>{
 const s=await basic({mode:'goal'});
 await s.transition({type:'answer_fact',key:'age',value:37});
 assert.ok(!s.result.candidates.some(p=>p.policy_id==='DEMO-JOB'));
 assert.ok(s.result.candidates.some(p=>p.policy_id==='DEMO-HOUSING'));
 await s.transition({type:'answer_fact',key:'age',value:null});
 assert.ok(s.result.candidates.some(p=>p.policy_id==='DEMO-JOB'));
});
test('empty and simulated data errors preserve a recoverable state',async()=>{
 const s=await basic(),before=structuredClone(s.result);
 s.scenario='error';
 await assert.rejects(s.transition({type:'answer_fact',key:'age',value:25}));
 assert.deepEqual(s.result,before);assert.equal(s.busy,false);
 s.scenario='normal';await s.transition({type:'answer_fact',key:'age',value:25});
 assert.equal(s.result.state.profile.age,25);
 s.scenario='empty';await s.transition({type:'show_results'});
 assert.deepEqual(s.result.candidates,[]);assert.equal(s.result.data_status,'ready');
 s.scenario='normal';await s.transition({type:'show_results'});
 assert.ok(s.result.candidates.length>0);
});
test('preferences do not change checks and preparation does not submit anything',async()=>{
 const s=await basic();await s.transition({type:'select_policy',policy_id:'DEMO-CENTER'});
 await s.transition({type:'choose_detail',accept:true});const before=s.result.candidates;
 await s.transition({type:'answer_demo',key:'available_time',value:'afternoon'});
 assert.deepEqual(s.result.candidates,before);
 await s.transition({type:'show_results'});await s.transition({type:'prepare'});
 assert.equal(s.result.state.stage,'preparation');
 await s.start();assert.deepEqual(s.detailAnswers,{});assert.equal(s.result.state.profile.age,null);
});
test('official references remain a separate, dated catalogue including closed notices',()=>{
 const c=JSON.parse(readFileSync(new URL('../demo/official-policies.json',import.meta.url),'utf8'));
 assert.equal(c.policies.length,6);assert.match(c.checked_on,/^\d{4}-\d{2}-\d{2}$/);
 for(const p of c.policies){assert.ok(p.reference_id.startsWith('REF-'));assert.ok(safeSourceUrl(p.url));assert.ok(p.period_note);}
 assert.equal(c.policies.filter(p=>p.availability==='referenced_notice_closed').length,2);
});
