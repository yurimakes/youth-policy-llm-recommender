import test from 'node:test';
import assert from 'node:assert/strict';
import {preparationDetails} from '../demo/preparation.mjs';

test('missing data does not invent documents, dates or application routes',()=>{
 const rows=preparationDetails({});
 assert.equal(rows.length,4);
 assert.ok(rows.every(([,value])=>value==='공고에서 확인 필요'));
 assert.equal(JSON.stringify(rows).includes('주민등록'),false);
});

test('partial periods remain partial without implying continuous applications',()=>{
 assert.equal(preparationDetails({application_start:'2026-10-01'})[0][1],'2026-10-01부터 · 종료일 확인 필요');
 assert.equal(preparationDetails({application_end:'2026-10-31'})[0][1],'시작일 확인 필요 · 2026-10-31까지');
 assert.equal(preparationDetails({application_start:'상시'})[0][1],'공고에서 확인 필요');
});

test('source strings remain literal and blank fields remain unknown',()=>{
 const rows=preparationDetails({application_start:'2026-10-01',application_end:'2026-10-31',required_documents:'<script>example</script>',application_method:'기관 방문',contact:' '});
 assert.equal(rows[0][1],'2026-10-01 ~ 2026-10-31');
 assert.equal(rows[1][1],'<script>example</script>');
 assert.equal(rows[2][1],'기관 방문');
 assert.equal(rows[3][1],'공고에서 확인 필요');
});
