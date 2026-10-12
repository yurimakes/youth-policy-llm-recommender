// Stored policy fields are descriptive source data, not verified application advice.
export function preparationDetails(candidate) {
 const recorded=value=>typeof value==='string'&&value.trim()?value.trim():'공고에서 확인 필요';
 const date=value=>typeof value==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(value)?value:null;
 const start=date(candidate.application_start),end=date(candidate.application_end);
 const period=start&&end?`${start} ~ ${end}`:start?`${start}부터 · 종료일 확인 필요`:end?`시작일 확인 필요 · ${end}까지`:'공고에서 확인 필요';
 return [
  ['기록된 신청기간',period],
  ['기록된 필요 서류',recorded(candidate.required_documents)],
  ['기록된 신청방법',recorded(candidate.application_method)],
  ['기록된 문의처',recorded(candidate.contact)]
 ];
}
