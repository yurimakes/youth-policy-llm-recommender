// 데모 목데이터 전용 진행. 실제 FastAPI 판정이나 공식 정책 조건을 대체하지 않는다.
export const DEMO_NOTICE = "화면 체험용 가상 정책·조건입니다. 실제 모집 공고나 신청 자격이 아니에요.";
export const MOCK_POLICIES = [
  {id:"DEMO-LIVING",name:"청년 활동지원금",icon:"₩",summary:"생활비와 다음 활동을 함께 준비해요",min:19,max:34,seoul:true,employment:"미취업자",household:true,topics:["living_cost","employment"]},
  {id:"DEMO-HOUSING",name:"청년 월세 지원",icon:"⌂",summary:"주거비 부담을 줄일 방법을 살펴봐요",min:19,max:39,seoul:true,household:true,topics:["living_cost","housing"]},
  {id:"DEMO-CENTER",name:"청년센터 첫 상담",icon:"…",summary:"어떤 지원이 필요한지 함께 정리해요",min:19,max:39,seoul:true,topics:["counseling","low_burden"]},
  {id:"DEMO-JOB",name:"취업 준비 프로그램",icon:"▣",summary:"나에게 맞는 취업 준비를 찾아봐요",min:19,max:34,employment:"미취업자",topics:["employment","low_burden"]},
  {id:"DEMO-WORKER",name:"재직 청년 교육비",icon:"▤",summary:"일하며 배울 수 있는 방법을 확인해요",min:19,max:39,employment:"중소기업 재직자",topics:["learning"]},
  {id:"DEMO-LEARNING",name:"직무 배움 프로그램",icon:"⚑",summary:"배우고 싶은 기술부터 시작해요",min:19,max:39,topics:["learning","low_burden"]}
];
const cards={situation:[['school','학교에 다녀요'],['working','일하고 있어요'],['resting','쉬고 있어요'],['unknown','답하기 어려워요']],interest:[['living_cost','생활비 부담 줄이기'],['low_burden','부담 적은 활동 찾기'],['counseling','사람에게 상담받기'],['unknown','잘 모르겠어요']],goal:[['employment','취업하기'],['housing','나만의 공간에서 생활하기'],['learning','새로운 기술 배우기'],['unknown','잘 모르겠어요']]};
const labels={confirmed:'확인됨',not_met:'미충족',check_required:'확인 필요',input_missing:'입력 부족'};
const option=(value,label)=>({value,label});
const questions={
 region_code:{key:'region_code',prompt:'지금 서울에\n살고 있나요?',purpose:'가상 지원의 지역 조건을 비교해요. 답하지 않으면 확인 필요로 남겨요.',input_type:'selection',options:[option('11000','네, 서울에 살아요'),option('26000','아니요, 다른 지역이에요')]},
 age:{key:'age',prompt:'만 나이를\n알려주세요.',purpose:'가상 지원의 나이 조건을 비교하기 위해 필요해요. 모르면 건너뛰어도 괜찮아요.',input_type:'integer',options:[]},
 employment_status:{key:'employment_status',prompt:'현재 취업 상태를\n확인해 주세요.',purpose:'앞서 고른 상황과 별개로 확인해요. 상황 카드만으로 추정하지 않아요.',input_type:'selection',options:[option('미취업자','지금은 취업하지 않았어요'),option('중소기업 재직자','중소기업에서 일하고 있어요'),option('대기업 재직자','대기업에서 일하고 있어요'),option('자영업자','사업을 하고 있어요')]},
 household:{key:'household',prompt:'함께 사는\n가족이 있나요?',purpose:'가상 데모의 가구 답변을 정리해요. 가족 이름이나 소득 금액은 묻지 않아요.',input_type:'demo_selection',options:[option('alone','혼자 살아요'),option('parents','부모님과 살아요'),option('others','다른 사람과 살아요')]},
 available_time:{key:'available_time',prompt:'참여하기 편한\n시간이 있나요?',purpose:'선호는 상담 요약에만 사용해요. 지원 자격을 결정하지 않아요.',input_type:'demo_selection',options:[option('weekday','평일 낮이 편해요'),option('afternoon','평일 오후가 편해요'),option('weekend','저녁·주말이 편해요'),option('either','아직 정하지 않았어요')]}
};
const check=(field,status,reason)=>({field,status,status_label:labels[status],reason});
export class DemoSession {
 constructor(){this.result=null;this.busy=false;this.scenario='normal';this.detailAnswers={};this.detailSkipped=new Set();}
 async start(mode='situation'){
  if(this.busy)throw new Error('이전 요청을 기다려 주세요.');
  this.detailAnswers={};this.detailSkipped.clear();
  this.result=this.response({start_mode:mode,stage:'start',cards:{},profile:{age:null,region_code:null,employment_status:null},preferences:{},answered:[],skipped:[],interested_policy_id:null,detail_choice:null,detail_paused:false,revision:0});
  return this.result;
 }
 assess(p,state){
  const u=state.profile;
  const checks=[check('application','check_required','모집 기간은 데모에서 확인하지 않아요. 실제 공고를 따로 확인해 주세요.')];
  checks.push(check('age',u.age===null?'input_missing':u.age<p.min||u.age>p.max?'not_met':'confirmed',`가상 조건: 만 ${p.min}~${p.max}세. 실제 정책의 연령 기준이 아니에요.`));
  checks.push(check('region_code',!p.seoul?'check_required':u.region_code===null?'input_missing':u.region_code.startsWith('11')?'confirmed':'not_met',p.seoul?'가상 조건: 서울 거주. 실제 공고와는 별개예요.':'실제 지원 지역은 공식 공고에서 확인해 주세요.'));
  checks.push(check('employment_status',!p.employment?'check_required':u.employment_status===null?'input_missing':u.employment_status===p.employment?'confirmed':'not_met',p.employment?`가상 조건: ${p.employment}. 상황 카드로 추정하지 않아요.`:'취업 상태의 실제 조건은 공식 공고에서 확인해 주세요.'));
  if(p.household)checks.push(check('household',this.detailAnswers.household?'confirmed':'input_missing','가상 데모의 가구 답변 여부만 표시해요. 실제 가구 자격을 판정하지 않아요.'));
  checks.push(check('income','check_required','소득·가구 기준과 예외는 공식 공고나 담당 기관에서 확인해야 해요.'));
  return checks;
 }
 candidates(state){
  if(['start','interest'].includes(state.stage)||this.scenario==='empty')return [];
  return MOCK_POLICIES.map(p=>{
   const checks=this.assess(p,state);
   return {policy_id:p.id,policy_name:p.name,summary:p.summary,benefit_text:null,icon:p.icon,status:'check_required',status_label:'확인 필요',checks,next_actions:['실제 모집 공고의 기간을 확인해 주세요.','필요한 서류·소득 기준을 담당 기관에 확인해 주세요.'],source_name:'가상 데모 데이터',source_url:null,last_verified_at:'2026-10-07T09:00:00Z'};
  }).filter(p=>!p.checks.some(c=>c.status==='not_met'));
 }
 question(state){
  if(['start','interest'].includes(state.stage)){
   const key=state.stage==='start'?state.start_mode:'interest';
   const prompt={situation:'요즘 어떻게\n지내고 있나요?',interest:'요즘 가장\n신경 쓰이는 건 뭐예요?',goal:'지금 가장 이루고\n싶은 것은 무엇인가요?'}[key];
   return {key,prompt,purpose:key==='situation'?'길게 설명하지 않아도 괜찮아요.\n지금 상태 하나만 골라주세요.':'가장 가까운 것 하나만 골라주세요.',input_type:'card',options:cards[key].map(([value,label])=>option(value,label)),allow_skip:true};
  }
  const candidates=this.candidates(state);
  const done=k=>state.answered.includes(k)||state.skipped.includes(k);
  if(state.stage==='basic')return candidates.length?['region_code','age'].filter(k=>!done(k)).map(k=>({...questions[k],allow_skip:true}))[0]||null:null;
  if(state.stage==='detail'){
   const p=MOCK_POLICIES.find(p=>p.id===state.interested_policy_id);
   if(!candidates.some(c=>c.policy_id===p?.id))return null;
   const keys=[...(p.household?['household']:[]),...(p.employment?['employment_status']:[]),'available_time'];
   const key=keys.find(k=>k in state.profile?!done(k):!this.detailAnswers[k]&&!this.detailSkipped.has(k));
   return key?{...questions[key],allow_skip:true}:null;
  }
  return null;
 }
 response(state){
  const candidates=this.candidates(state);
  const useful=this.question({...state,stage:'detail'});
  return {api_version:'1',state,next_question:this.question(state),candidates,data_status:['start','interest'].includes(state.stage)?'not_loaded':'ready',detail_offer_available:state.stage==='results'&&!!state.interested_policy_id&&state.detail_choice===null&&!!useful,selected_policy_excluded:!!state.interested_policy_id&&!candidates.some(p=>p.policy_id===state.interested_policy_id),can_show_results:!['start','interest'].includes(state.stage),notice:DEMO_NOTICE};
 }
 async transition(action){
  if(this.busy)throw new Error('이전 요청을 기다려 주세요.');
  if(!this.result)throw new Error('먼저 시작해 주세요.');
  this.busy=true;
  try{
   const s=structuredClone(this.result.state),type=action.type;
   if(this.scenario==='error'&&!['start','interest'].includes(s.stage))throw new Error('안내를 불러오지 못했어요. 체험 상황을 기본 흐름으로 바꾼 뒤 다시 시도해 주세요. 이전 답변은 그대로예요.');
   if(this.scenario==='error'&&type==='choose_card'&&(s.stage==='interest'||s.start_mode==='goal'))throw new Error('안내를 불러오지 못했어요. 기본 흐름으로 바꾼 뒤 다시 시도해 주세요. 이전 답변은 그대로예요.');
   const mark=(key,value)=>{s.answered=s.answered.filter(k=>k!==key);s.skipped=s.skipped.filter(k=>k!==key);(value===null||value==='unknown'?s.skipped:s.answered).push(key);};
   if(type==='choose_card'){
    if(!cards[action.key]?.some(([v])=>v===action.value)&&action.value!==null)throw new Error('선택값을 확인해 주세요.');
    if(action.value===null)delete s.cards[action.key];else s.cards[action.key]=action.value;
    mark(action.key,action.value);s.stage=action.key==='situation'&&s.stage==='start'?'interest':'basic';
    s.interested_policy_id=null;s.detail_choice=null;s.detail_paused=false;
   }else if(type==='answer_fact'){
    if(!(action.key in s.profile))throw new Error('입력 항목을 확인해 주세요.');
    if(action.value!==null){
     if(action.key==='age'&&(!Number.isInteger(action.value)||action.value<0||action.value>120))throw new Error('만 나이를 0~120의 정수로 입력해 주세요.');
     if(action.key==='region_code'&&!/^\d{5}$/.test(action.value))throw new Error('지역 선택을 확인해 주세요.');
     if(action.key==='employment_status'&&!questions.employment_status.options.some(o=>o.value===action.value))throw new Error('취업 상태 선택을 확인해 주세요.');
    }
    s.profile[action.key]=action.value;mark(action.key,action.value);
   }else if(type==='answer_demo'){
    if(s.stage!=='detail'||!['household','available_time'].includes(action.key))throw new Error('상세 확인에서만 답할 수 있어요.');
    if(action.value!==null&&!questions[action.key].options.some(o=>o.value===action.value))throw new Error('답변을 확인해 주세요.');
    if(action.value===null){delete this.detailAnswers[action.key];this.detailSkipped.add(action.key);}else{this.detailAnswers[action.key]=action.value;this.detailSkipped.delete(action.key);}
   }else if(type==='show_results'){s.stage='results';s.detail_paused=false;
   }else if(type==='select_policy'){
    if(s.stage!=='results'||!this.candidates(s).some(p=>p.policy_id===action.policy_id))throw new Error('현재 후보에서 선택해 주세요.');
    if(s.interested_policy_id!==action.policy_id){s.interested_policy_id=action.policy_id;s.detail_choice=null;s.detail_paused=false;}
   }else if(type==='choose_detail'){
    if(s.stage!=='results'||!this.candidates(s).some(p=>p.policy_id===s.interested_policy_id))throw new Error('정책을 먼저 선택해 주세요.');
    if(typeof action.accept!=='boolean')throw new Error('상세 확인 선택을 확인해 주세요.');
    s.detail_choice=action.accept;s.detail_paused=false;s.stage=action.accept&&this.question({...s,stage:'detail'})?'detail':'results';
   }else if(type==='pause_detail'){if(s.stage!=='detail')throw new Error('상세 진행을 확인해 주세요.');s.stage='results';s.detail_paused=true;
   }else if(type==='resume_detail'){
    if(!s.detail_paused||!this.candidates(s).some(p=>p.policy_id===s.interested_policy_id))throw new Error('이어갈 상세 확인이 없어요.');
    s.stage='detail';s.detail_paused=false;
   }else if(type==='prepare'){if(s.stage!=='results')throw new Error('먼저 결과를 확인해 주세요.');s.stage='preparation';
   }else throw new Error('진행 항목을 확인해 주세요.');
   s.revision++;this.result=this.response(s);return this.result;
  }finally{this.busy=false;}
 }
}
