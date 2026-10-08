import {IntakeSession,safeSourceUrl,formatVerifiedAt} from './client.mjs';
import {DemoSession,MOCK_POLICIES} from './mock.mjs';

const mock=document.body.dataset.runtime==='mock';
const session=mock?new DemoSession():new IntakeSession();
const $=id=>document.getElementById(id);
const facts={age:'만 나이',region_code:'거주 지역',employment_status:'취업 상태'};
const fields={...facts,application:'신청 기간',household:'가구',income:'소득',education:'학력',eligibility:'추가 조건'};
const icons={school:'▰',working:'▣',resting:'☕',unknown:'?',living_cost:'₩',low_burden:'⚑',counseling:'…',employment:'▣',housing:'⌂',learning:'▤'};
const descriptions={unknown:'괜찮아요. 여러 방향을 함께 보여드릴게요.'};
const options=new Map();
let selected=new Set(),knownCandidates=new Map(),completed=new Map(),activePolicy=null;
let page='intake',updated=false,busy=false,retry=null,draft=null,history=[],documentKind='summary',toastTimer;
const create=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;};
const button=(label,callback,cls='primary')=>{const n=create('button',cls,label);n.type='button';n.addEventListener('click',callback);return n;};
const para=(text,cls='subtitle')=>create('p',cls,text);
const chosen=()=>session.result?.candidates.filter(c=>selected.has(c.policy_id))||[];
function toast(message){$('toast').textContent=message;$('toast').hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{$('toast').hidden=true;},3000);}
function snapshot(){return session.result?{result:structuredClone(session.result),selected:[...selected],page,updated,activePolicy,detailAnswers:mock?{...session.detailAnswers}:null,detailSkipped:mock?[...session.detailSkipped]:null}:null;}
function restore(s){session.result=s.result;selected=new Set(s.selected);page=s.page;updated=s.updated;activePolicy=s.activePolicy;if(mock){session.detailAnswers=s.detailAnswers;session.detailSkipped=new Set(s.detailSkipped);}render();}
function disabled(value){
 $('loading').hidden=!value;$('main').setAttribute('aria-busy',String(value));
 document.querySelectorAll('button,input,select').forEach(n=>{if(value){n.dataset.wasDisabled=String(n.disabled);n.disabled=true;}else if(n.dataset.wasDisabled!==undefined){n.disabled=n.dataset.wasDisabled==='true';delete n.dataset.wasDisabled;}});
}
async function perform(operation,after=()=>{}){
 if(busy)return false;
 busy=true;$('error').hidden=true;$('edit-error').hidden=true;const previous=snapshot();disabled(true);
 try{
  await operation();
  if(session.result.state.stage==='detail')updated=true;
  if(['basic','detail'].includes(session.result.state.stage)&&!session.result.next_question){
   if(session.result.state.stage==='detail')updated=true;
   await session.transition({type:'show_results'});
  }
  if(previous)history.push(previous);
  disabled(false);busy=false;reconcile();after();render();retry=null;
  if(!$('edit-dialog').open&&!$('detail-dialog').open)$('screen').querySelector('h1')?.focus();
  return true;
 }catch(e){
  const message=e instanceof TypeError||e instanceof SyntaxError?'안내를 불러오지 못했어요. 서버 연결 상태를 확인하고 다시 시도해 주세요.':e.message;
  retry=()=>perform(operation,after);$('error-text').textContent=message;$('error').hidden=false;
  if($('edit-dialog').open){$('edit-error').textContent=message;$('edit-error').hidden=false;}
  else $('error').scrollIntoView({block:'nearest'});
  return false;
 }finally{disabled(false);busy=false;}
}
const transition=(action,after)=>perform(()=>session.transition(action),after);
function reconcile(){
 const ids=new Set(session.result.candidates.map(c=>c.policy_id));
 if(!['start','interest'].includes(session.result.state.stage))selected=new Set([...selected].filter(id=>ids.has(id)));
 session.result.candidates.forEach(c=>knownCandidates.set(c.policy_id,c));
 if(activePolicy&&!ids.has(activePolicy))activePolicy=chosen()[0]?.policy_id||null;
}
function heading(eyebrow,title,description){const h=create('h1','',title);h.tabIndex=-1;$('screen').append(para(eyebrow,'eyebrow'),h);if(description)$('screen').append(para(description));}
function bottom(primary,action,{secondary,secondaryAction,skip,skipAction,disabled:off=false,note}={}){
 $('bottom').replaceChildren();
 if(secondary)$('bottom').append(button(secondary,secondaryAction,'secondary'));
 const next=button(primary,action);next.disabled=off;$('bottom').append(next);
 if(skip)$('bottom').append(button(skip,skipAction,'text-button full'));
 if(note)$('screen').append(para(note,'muted'));
 return next;
}
function row(key,value,uncertain=false){const n=create('div','info-row');n.append(create('span','',key),create('span',uncertain?'uncertain':'',value));return n;}
function optionLabel(key,value){if(value===null||value===undefined)return '모름 · 건너뛰기';if(key==='age')return `만 ${value}세`;return options.get(key)?.find(o=>o.value===value)?.label||value;}
function chips(){
 $('chips').replaceChildren();const s=session.result.state;
 const cardLabels={situation:{school:'학교에 다녀요',working:'일하고 있어요',resting:'쉬고 있어요',unknown:'답하기 어려워요'},interest:{living_cost:'생활비 부담',low_burden:'부담 적은 활동',counseling:'상담',unknown:'관심 모름'},goal:{employment:'취업',housing:'주거',learning:'배움',unknown:'목표 모름'}};
 for(const [key,value] of Object.entries(s.cards)){$('chips').append(button(cardLabels[key]?.[value]||value,()=>openEdit(key),'chip'));}
 for(const key of Object.keys(facts).filter(k=>s.answered.includes(k)||s.skipped.includes(k))){$('chips').append(button(optionLabel(key,s.profile[key]),()=>openEdit(key),'chip'));}
 $('chips').hidden=s.stage==='start'||page==='document';
}
function cardOptions(question,container){
 draft=null;const list=create('div','card-list');
 for(const o of question.options){
  const label=create('label','choice-card'+(o.value==='unknown'?' unknown':''));
  const input=create('input');input.type='radio';input.name='current-answer';input.value=o.value;input.setAttribute('aria-label',o.label);
  const body=create('span','card-content');body.append(create('strong','',o.label));if(descriptions[o.value])body.append(create('small','',descriptions[o.value]));
  label.append(input,create('span','card-icon',icons[o.value]||'·'),body,create('span','radio-mark','✓'));
  input.addEventListener('change',()=>{draft=o.value;$('bottom').querySelector('.primary').disabled=false;});list.append(label);
 }
 container.append(list);
}
function factInput(question,container,prefix='answer',current=null){
 options.set(question.key,question.options);
 if(question.input_type==='integer'){
  const form=create('form');form.id='current-form';const label=create('label','muted','만 나이');label.htmlFor=prefix+'-value';
  const input=create('input');input.type='number';input.min='0';input.max='120';input.step='1';input.inputMode='numeric';input.required=true;input.placeholder='만 나이를 입력해 주세요';input.id=prefix+'-value';input.value=current??'';
  form.append(label,input);container.append(form);form.addEventListener('submit',e=>{e.preventDefault();submitAnswer(question);});
 }else if(question.input_type==='region_code'){
  const label=create('label','muted','실제 거주 지역');label.htmlFor=prefix+'-value';const select=create('select');select.id=prefix+'-value';select.required=true;
  const choices=[{value:'',label:'선택해 주세요'},...question.options,{value:'__manual__',label:'목록에 없는 지역 · 5자리 코드 직접 입력'}];
  choices.forEach(o=>{const n=create('option','',o.label);n.value=o.value;select.append(n);});
  select.value=current??'';const manual=create('input','manual-region');manual.id=prefix+'-manual';manual.type='text';manual.inputMode='numeric';manual.pattern='[0-9]{5}';manual.maxLength=5;manual.placeholder='실제 거주 지역 5자리 코드';manual.setAttribute('aria-label','실제 거주 지역 5자리 코드');
  const toggle=()=>{manual.hidden=select.value!=='__manual__';manual.disabled=manual.hidden;manual.required=!manual.hidden;};select.addEventListener('change',toggle);toggle();container.append(label,select,manual,para('목록은 전체 지역이 아니에요. 코드를 모르면 건너뛰어도 괜찮아요.','muted'));
 }else cardOptions(question,container);
}
function submitAnswer(q,value){
 if(value===undefined){
  if(['card','selection','demo_selection'].includes(q.input_type)){if(draft===null)return;value=draft;}
  else{const input=$('answer-value');if(!input.reportValidity())return;value=q.key==='age'?Number(input.value):input.value==='__manual__'?$('answer-manual').value:input.value;if(q.input_type==='region_code'&&input.value==='__manual__'&&!$('answer-manual').reportValidity())return;}
 }
 const type=q.input_type==='card'?'choose_card':q.input_type==='demo_selection'?'answer_demo':'answer_fact';
 transition({type,key:q.key,value},()=>{page='intake';});
}
function intake(){
 const r=session.result,q=r.next_question,s=r.state;
 if(!q)return;
 if(q.input_type!=='card')options.set(q.key,q.options);
 const title=s.stage==='start'?'지원 찾기':s.stage==='interest'?'지원 찾기':s.stage==='detail'?'자세히 확인하기':'기초 확인';$('page-title').textContent=title;
 $('progress').hidden=!['basic','detail'].includes(s.stage);$('progress-fill').style.width=s.stage==='basic'?(q.key==='region_code'?'50%':'100%'):'60%';
 const eyebrow=s.stage==='start'?'내게 맞는 지원':s.stage==='interest'?'지금 가장 가까운 것':s.stage==='detail'?'선택한 지원을 조금 더 확인해요':'필요한 정보만 하나씩';
 heading(eyebrow,q.prompt,q.purpose);
 if(s.stage==='start'){
  const modes=create('div','mode-switch');for(const [mode,label]of [['situation','상황부터 둘러보기'],['goal','목표부터 찾아보기']])modes.append(button(label,()=>start(mode),mode===s.start_mode?'active':''));$('screen').append(modes);
 }
 factInput(q,$('screen'));
 const isCard=['card','selection','demo_selection'].includes(q.input_type);
 bottom('다음',()=>submitAnswer(q),{disabled:isCard,skip:'답하지 않고 넘어가기',skipAction:()=>submitAnswer(q,null)});
 if(s.stage==='detail')$('screen').append(button('상세 확인 잠시 멈추기',()=>transition({type:'pause_detail'},()=>{updated=true;page='updated';}),'text-button'));
 else if(r.can_show_results)$('screen').append(button('지금 정보로 결과 보기',()=>transition({type:'show_results'},()=>{page='directions';}),'text-button'));
}
function checkDetails(candidate){
 const details=create('details','condition-details');details.append(create('summary','','조건별 확인사항과 근거'));const list=create('ul','condition-list');
 candidate.checks.forEach(c=>{const li=create('li');const top=create('div','condition-top');top.append(create('span','',fields[c.field]||'확인 항목'),create('strong','',c.status==='confirmed'?'개별 조건 확인됨':c.status_label));li.append(top,create('span','reason',c.reason));list.append(li);});details.append(list);
 const meta=create('p','policy-meta',candidate.source_name+' · 데이터 처리 기준 '+formatVerifiedAt(candidate.last_verified_at));const url=safeSourceUrl(candidate.source_url);
 if(url){const a=create('a','','공식 공고 확인하기');a.href=url;a.target='_blank';a.rel='noopener noreferrer';meta.append(a);}else meta.append(create('span','',mock?' · 가상 정책의 공식 공고는 없어요.':' · 공식 공고는 제공기관에서 확인해 주세요.'));
 details.append(meta);return details;
}
function policyChoice(c,{detailed=false,excluded=false}={}){
 const wrapper=create('article');const btn=create('button','policy-choice'+(selected.has(c.policy_id)?' selected':'')+(excluded?' excluded':''));btn.type='button';btn.disabled=excluded;btn.setAttribute('aria-pressed',String(selected.has(c.policy_id)));
 const top=create('div','policy-heading'),body=create('span','card-content');body.append(create('strong','',c.policy_name+(mock?' · 예시':'')),create('small','',excluded?'현재 답변과 조건에 맞지 않아 제외됐어요.':c.summary||c.benefit_text||'조건과 남은 확인사항을 살펴보세요.'));
 const glyph=c.icon||(/월세|주거/.test(c.policy_name)?'⌂':/상담/.test(c.policy_name)?'…':'₩');top.append(create('span','card-icon',glyph),body,create('span','radio-mark','✓'));btn.append(top);
 if(detailed&&!excluded){
  const confirmed=c.checks.filter(x=>x.status==='confirmed').map(x=>fields[x.field]||x.field);
  const pending=c.checks.filter(x=>x.status!=='confirmed').map(x=>fields[x.field]||x.field);
  const info=create('div','condition-summary');info.append(row(confirmed.join(' · ')||'확인된 조건',confirmed.length?'개별 조건 확인됨':'입력 확인 전'),row('남은 확인',pending.slice(0,3).join(' · ')||'공식 최종 자격',true));btn.append(info);
 }
 btn.addEventListener('click',()=>{if(selected.has(c.policy_id))selected.delete(c.policy_id);else selected.add(c.policy_id);render();});wrapper.append(btn);
 if(detailed&&!excluded)wrapper.append(checkDetails(c));return wrapper;
}
async function chooseBasket(){
 const first=chosen()[0];if(!first)return;
 const ok=await transition({type:'select_policy',policy_id:first.policy_id},()=>{updated=true;page='updated';activePolicy=first.policy_id;});
 if(ok&&session.result.detail_offer_available)offerDetail();
}
function offerDetail(){
 const r=session.result,selectedPolicy=r.candidates.find(c=>c.policy_id===r.state.interested_policy_id);if(!selectedPolicy||!r.detail_offer_available)return;
 $('detail-title').textContent=selectedPolicy.policy_name+'을\n더 자세히 확인해볼까요?';$('detail-copy').textContent='필요한 조건만 조금 더 물어볼게요. 지금 정보로 결과를 봐도 괜찮아요.';
 $('detail-preview').replaceChildren(row('직접 확인한 정보','기존 답변 이어받기'),row('모르는 조건','확인 필요로 남기기'),row('편한 참여 방식','상담 요약에만 사용'));
 $('detail-actions').replaceChildren(button('더 자세히 확인하기',async()=>{const ok=await transition({type:'choose_detail',accept:true},()=>{page='intake';});if(ok)$('detail-dialog').close();}),button('지금 결과로 볼게요',async()=>{const ok=await transition({type:'choose_detail',accept:false},()=>{updated=true;page='updated';});if(ok)$('detail-dialog').close();},'text-button'));
 $('detail-dialog').showModal();
}
function directions(){
 const r=session.result,done=updated||page==='updated';$('page-title').textContent='지원 찾기';$('progress').hidden=true;
 heading(done?'다시 정리했어요':'확인해 볼 지원',done?'입력한 조건으로\n다시 확인했어요':'필요한 지원을\n함께 살펴볼까요?',done?'답변을 반영해 후보를 다시 확인했어요.':'아직 신청 자격이 확정된 건 아니에요.\n관심 있는 지원을 담아주세요.');
 const inline=create('div','inline-actions');inline.append(button('내 답변 수정',()=>openEdit(),'text-button blue'));
 if(r.state.detail_paused)inline.append(button('상세 확인 이어가기',()=>transition({type:'resume_detail'},()=>{page='intake';}),'text-button blue'));
 else if(done&&r.detail_offer_available)inline.append(button('추가 조건 확인하기',offerDetail,'text-button blue'));
 $('screen').append(inline);
 if(r.selected_policy_excluded)$('screen').append(para('선택했던 정책이 현재 후보에서 제외됐어요. 다른 지원을 골라주세요.','info-card blue muted'));
 const list=create('div','card-list');
 // 관심 분야는 가상 데모의 표시 순서에만 쓰며 자격 판정을 바꾸지 않는다.
 let candidates=[...r.candidates];if(mock){const key=r.state.cards.interest||r.state.cards.goal;candidates.sort((a,b)=>Number(MOCK_POLICIES.find(p=>p.id===b.policy_id)?.topics.includes(key))-Number(MOCK_POLICIES.find(p=>p.id===a.policy_id)?.topics.includes(key)));}
 candidates.forEach(c=>list.append(policyChoice(c,{detailed:done})));$('screen').append(list);
 if(!candidates.length){const empty=create('div','empty');empty.append(create('h2','','지금 정보로 안내할 후보가 없어요.'),para('입력한 조건이나 모집 기간에 따라 후보가 없을 수 있어요. 답변을 수정하거나 공식 지원 정보를 확인해 주세요.','muted'),button('공식 정책 참고자료 보기',openOfficial,'text-button blue'));$('screen').append(empty);}
 if(done){const excluded=[...knownCandidates.values()].filter(c=>!r.candidates.some(p=>p.policy_id===c.policy_id));if(excluded.length){$('screen').append(para('현재 답변으로 제외된 지원','section-label'));excluded.slice(0,3).forEach(c=>$('screen').append(policyChoice(c,{excluded:true})));}}
 $('screen').append(para(r.notice,'muted'));
 bottom(done?'담은 지원 준비하기':selected.size+'개 담기',done?()=>transition({type:'prepare'},()=>{page='preparation';activePolicy=chosen()[0]?.policy_id;}):chooseBasket,{disabled:selected.size===0,note:done?'담은 지원은 이 화면이 열려 있는 동안만 유지돼요.':'여러 개 담을 수 있어요.'});
}
function currentPolicy(){const list=chosen();return list.find(c=>c.policy_id===activePolicy)||list[0]||null;}
const taskDefinitions=[{key:'period',title:'신청 기간 확인하기',description:'공식 공고에서 현재 모집 여부를 확인해요.',icon:'◷'},{key:'documents',title:'필요한 서류 확인하기',description:'공고의 서류 목록과 발급 경로를 살펴봐요.',icon:'▤'},{key:'questions',title:'남은 조건 물어보기',description:'공고만으로 확인하기 어려운 항목을 정리해요.',icon:'…'}];
function tasksFor(c){return completed.get(c.policy_id)||new Set();}
function preparation(){
 $('page-title').textContent='지원장바구니';$('progress').hidden=true;
 const c=currentPolicy();if(!c){heading('담은 지원이 없어요','지원부터\n골라볼까요?');bottom('지원 결과로 돌아가기',()=>transition({type:'show_results'},()=>{page='updated';}));return;}
 activePolicy=c.policy_id;const tasks=tasksFor(c),remaining=taskDefinitions.length-tasks.size;
 heading('담은 지원 '+chosen().length+'개',remaining?'준비할 일이\n'+remaining+'개 남았어요':'확인한 내용을\n상담에 가져가세요',null);
 const tabs=create('div','basket-tabs');chosen().forEach(p=>tabs.append(button(p.policy_name,()=>{activePolicy=p.policy_id;render();},p.policy_id===c.policy_id?'active':'')));$('screen').append(tabs);
 const list=create('div','card-list');for(const t of taskDefinitions){
  const label=create('label','task-card'+(tasks.has(t.key)?' done':''));const input=create('input');input.type='checkbox';input.checked=tasks.has(t.key);input.setAttribute('aria-label',t.title+' 완료 표시');input.style.position='absolute';input.style.opacity='0';input.style.width='1px';input.style.height='1px';
  const body=create('span','card-content');body.append(create('strong','',t.title),create('small','',tasks.has(t.key)?'내가 확인했어요.':t.description));label.append(input,create('span','card-icon',t.icon),body,create('span','radio-mark','✓'));
  input.addEventListener('change',()=>{const next=new Set(tasks);if(input.checked)next.add(t.key);else next.delete(t.key);completed.set(c.policy_id,next);render();});list.append(label);
 }
 $('screen').append(list,para('준비 문서','section-label'));
 const tools=create('div','doc-tools');for(const [kind,title,icon]of [['checklist','체크리스트','▣'],['guidance','발급 안내','▤'],['summary','상담 요약서','▰'],['inquiry','문의 초안','✉']]){const b=button('',()=>{documentKind=kind;page='document';render();},'');b.append(create('span','card-icon',icon),create('span','',title));tools.append(b);}$('screen').append(tools,para('완료 표시는 내가 확인한 기록이에요. 기관의 확인이나 신청 완료를 뜻하지 않아요.','muted'));
 const source=safeSourceUrl(c.source_url);if(source){const a=create('a','muted','공식 공고 열기');a.href=source;a.target='_blank';a.rel='noopener noreferrer';$('screen').append(a);}else $('screen').append(button('실제 공식 정책 참고자료 보기',openOfficial,'text-button blue'));
 bottom('지원 결과로 돌아가기',()=>transition({type:'show_results'},()=>{page='updated';updated=true;}));
}
function makeDocument(){
 const c=currentPolicy();if(!c)return;
 const s=session.result.state,title={summary:'상담 요약서',checklist:'준비 체크리스트',guidance:'발급 안내',inquiry:'문의 초안'}[documentKind];$('page-title').textContent=title;$('progress').hidden=true;
 const doc=create('section','document');$('screen').append(doc);
 const eyebrow=mock?'가상 데모 기준 · '+new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul'}).format(new Date()):'데이터 처리 기준 · '+formatVerifiedAt(c.last_verified_at);
 const h=create('h1','',documentKind==='summary'?'상담할 때\n이 화면을 보여주세요':documentKind==='checklist'?'확인할 일을\n하나씩 준비해요':documentKind==='guidance'?'필요한 서류부터\n공고에서 확인해요':'문의할 내용을\n함께 정리했어요');h.tabIndex=-1;doc.append(para(eyebrow,'eyebrow'),h);
 const profile=create('div','info-card');profile.append(create('strong','','내가 직접 입력한 정보'));
 Object.entries(facts).forEach(([key,label])=>profile.append(row(label,optionLabel(key,s.profile[key]))));
 const situation={school:'학교에 다녀요',working:'일하고 있어요',resting:'쉬고 있어요',unknown:'답하기 어려워요'}[s.cards.situation];if(situation)profile.append(row('내 상황 카드',situation));
 if(mock){const family={alone:'혼자 살아요',parents:'부모님과 살아요',others:'다른 사람과 살아요'}[session.detailAnswers.household];if(family)profile.append(row('가구 답변',family));const pref={weekday:'평일 낮',afternoon:'평일 오후',weekend:'저녁·주말',either:'아직 정하지 않음'}[session.detailAnswers.available_time];if(pref)profile.append(row('선호 · 자격에 사용 안 함',pref));}
 doc.append(profile);
 const policy=create('div','info-card');policy.append(create('strong','',c.policy_name+(mock?' · 가상 예시':'')));
 const confirmed=c.checks.filter(x=>x.status==='confirmed').map(x=>fields[x.field]||x.field),pending=c.checks.filter(x=>x.status!=='confirmed').map(x=>fields[x.field]||x.field);
 policy.append(row('개별 조건 확인',confirmed.join(' · ')||'아직 확인된 조건 없음'),row('확인 필요',pending.join(' · '),true));doc.append(policy);
 const questions=create('div','info-card');questions.append(create('strong','',documentKind==='checklist'?'다음 확인할 항목':documentKind==='guidance'?'공식 발급 경로 확인 순서':'담당 기관에 물어볼 것'));
 const lines=documentKind==='checklist'?taskDefinitions.map(t=>(tasksFor(c).has(t.key)?'확인함 · ':'미확인 · ')+t.title):documentKind==='guidance'?['정책 공고에서 제출해야 하는 서류 목록을 먼저 확인하세요.','발급 주체와 온라인·방문 발급 가능 여부를 공식 공고나 기관에 확인하세요.','주민등록등본 등 특정 서류가 필수라고 미리 단정하지 않아요.']:['현재 모집 중인지, 제 조건으로 어떤 절차를 확인하면 될까요?','확인되지 않은 '+pending.slice(0,3).join('·')+' 항목은 어떻게 확인하나요?','필요한 서류와 공식 발급 경로를 알려주실 수 있나요?'];
 const list=create('ol');lines.forEach(t=>list.append(create('li','',t)));questions.append(list);doc.append(questions);
 if(documentKind==='inquiry')doc.append(para('안녕하세요. '+c.policy_name+'에 관심이 있습니다. 위에 정리한 조건을 바탕으로 모집 여부·자격·필요 서류를 확인하고 싶습니다. 안내 부탁드립니다.','info-card muted'));
 const source=safeSourceUrl(c.source_url);if(source){const a=create('a','policy-meta','공식 공고: '+source);a.href=source;a.target='_blank';a.rel='noopener noreferrer';doc.append(a);}
 doc.append(para(c.notice||session.result.notice,'document-footer'),para('외부 AI 없이 입력과 확인사항을 모은 초안이에요. 직접 검토한 뒤 필요할 때 전달하세요.','document-footer'));
 bottom('PDF로 저장',()=>window.print(),{secondary:'복사하기',secondaryAction:()=>copyDocument()});$('screen').append(para('PDF로 저장을 누르면 인쇄창이 열려요. 저장 대상을 PDF로 선택해 주세요.','muted print-hint'));
}
async function copyDocument(){const text=$('screen').querySelector('.document')?.innerText||'';try{await navigator.clipboard.writeText(text);toast('내용을 복사했어요.');}catch{toast('자동 복사를 사용할 수 없어요. 내용을 선택해 복사해 주세요.');}}
function render(){
 if(!session.result)return;$('screen').replaceChildren();$('bottom').replaceChildren();chips();
 $('basket-count').textContent=selected.size;$('basket-count').hidden=selected.size===0;$('basket-button').hidden=selected.size===0;
 const s=session.result.state;$('back').hidden=s.stage==='start'&&page==='intake';
 if(page==='document')makeDocument();else if(page==='preparation'||s.stage==='preparation')preparation();else if(s.stage==='results')directions();else intake();
}
function editInput(){
 const key=$('edit-key').value,container=$('edit-input');container.replaceChildren();let input;
 if(key==='age'){input=create('input');input.type='number';input.min='0';input.max='120';input.step='1';input.inputMode='numeric';input.value=session.result.state.profile.age??'';}
 else{input=create('select');const choices=[...(options.get(key)||[])];if(key==='region_code'&&!mock)choices.push({value:'__manual__',label:'목록에 없는 지역 · 5자리 코드 직접 입력'});const blank=create('option','','선택해 주세요');blank.value='';input.append(blank);choices.forEach(o=>{const n=create('option','',o.label);n.value=o.value;input.append(n);});const current=session.result.state.profile[key];input.value=key==='region_code'&&!mock&&current&&!choices.some(o=>o.value===current)?'__manual__':current??'';}
 input.id='edit-value';input.required=true;input.setAttribute('aria-label',facts[key]||key);container.append(input);
 if(key==='region_code'&&!mock){const manual=create('input','manual-region');manual.id='edit-manual';manual.inputMode='numeric';manual.pattern='[0-9]{5}';manual.maxLength=5;manual.value=session.result.state.profile[key]??'';manual.setAttribute('aria-label','실제 거주 지역 5자리 코드');container.append(manual);input.addEventListener('change',updateEditDisabled);}
 $('edit-unknown').checked=session.result.state.profile[key]===null;updateEditDisabled();
}
function updateEditDisabled(){const unknown=$('edit-unknown').checked;$('edit-value').disabled=unknown;const manual=$('edit-manual');if(manual){manual.hidden=$('edit-value').value!=='__manual__';manual.disabled=unknown||manual.hidden;manual.required=!manual.disabled;}}
function openEdit(key){
 if(!session.result)return;
 if(key&&key in session.result.state.cards){toast('위쪽 이전 버튼으로 카드 선택을 다시 시작할 수 있어요.');return;}
 const touched=Object.keys(facts).filter(k=>session.result.state.answered.includes(k)||session.result.state.skipped.includes(k));if(!touched.length){toast('아직 수정할 기초 답변이 없어요.');return;}
 $('edit-key').replaceChildren(...touched.map(k=>{const n=create('option','',facts[k]);n.value=k;return n;}));if(key&&touched.includes(key))$('edit-key').value=key;$('edit-error').hidden=true;editInput();$('edit-dialog').showModal();
}
async function openOfficial(){
 $('help-dialog').close();$('official-dialog').showModal();$('official-list').replaceChildren(para('공식 자료를 불러오고 있어요.','muted'));
 try{
  const r=await fetch('/demo/assets/official-policies.json',{cache:'no-store',credentials:'omit'});if(!r.ok)throw new Error('unavailable');const catalogue=await r.json();$('official-list').replaceChildren();
  for(const p of catalogue.policies){const url=safeSourceUrl(p.url);if(!url)continue;const section=create('section','official-item');const a=create('a','',p.name);a.href=url;a.target='_blank';a.rel='noopener noreferrer';section.append(a,para(p.summary,'muted'),para(p.period_note+' · 페이지 확인 '+catalogue.checked_on,'muted'));$('official-list').append(section);}
 }catch{$('official-list').replaceChildren(para('공식 참고자료를 불러오지 못했어요. 잠시 후 다시 열어주세요.','muted'));}
}
async function start(mode='situation'){
 const ok=await perform(()=>session.start(mode),()=>{selected=new Set();knownCandidates=new Map();completed=new Map();activePolicy=null;page='intake';updated=false;options.clear();history=[];});
 if(ok){$('help-dialog').close();$('detail-dialog').close();}
}
$('retry').addEventListener('click',()=>retry?.());$('help').addEventListener('click',()=>{$('help-dialog').showModal();});$('help-close').addEventListener('click',()=>{$('help-dialog').close();});$('official-button').addEventListener('click',openOfficial);$('official-close').addEventListener('click',()=>{$('official-dialog').close();});
$('restart').addEventListener('click',()=>{if(window.confirm('입력한 내용과 담은 지원을 지우고 처음부터 시작할까요?'))start();});
$('back').addEventListener('click',()=>{if(busy)return;if(page==='document'){page='preparation';render();}else if(page==='preparation'||session.result.state.stage==='preparation')transition({type:'show_results'},()=>{page='updated';});else if(history.length)restore(history.pop());else start();});
$('basket-button').addEventListener('click',()=>{if(session.result.state.stage==='results')transition({type:'prepare'},()=>{page='preparation';activePolicy=chosen()[0]?.policy_id;});else if(session.result.state.stage==='preparation'){page='preparation';render();}else toast('질문을 마친 뒤 담은 지원을 준비할 수 있어요.');});
$('edit-key').addEventListener('change',editInput);$('edit-unknown').addEventListener('change',updateEditDisabled);$('edit-close').addEventListener('click',()=>{$('edit-dialog').close();});
$('edit-form').addEventListener('submit',async e=>{e.preventDefault();const key=$('edit-key').value,value=$('edit-unknown').checked?null:key==='age'?Number($('edit-value').value):$('edit-value').value==='__manual__'?$('edit-manual').value:$('edit-value').value;const ok=await transition({type:'answer_fact',key,value});if(ok){$('edit-dialog').close();toast('수정한 조건으로 다시 확인했어요.');}});
$('detail-dialog').addEventListener('cancel',e=>{e.preventDefault();transition({type:'choose_detail',accept:false},()=>{$('detail-dialog').close();page='updated';});});
$('scenario').addEventListener('change',()=>{if(mock)session.scenario=$('scenario').value;});
$('demo-banner').hidden=!mock;$('demo-controls').hidden=!mock;
start();
