import {test,expect} from '@playwright/test';
import {mkdirSync} from 'node:fs';

const choose=async(page,name)=>{
 const radio=page.getByRole('radio',{name,exact:true});
 await page.locator('.choice-card').filter({has:radio}).click();
 await expect(radio).toBeChecked();
 await page.getByRole('button',{name:'다음',exact:true}).click();
};
async function basic(page){
 await page.goto('/');
 await expect(page.locator('#demo-banner')).toBeVisible();
 await choose(page,'쉬고 있어요');
 await choose(page,'생활비 부담 줄이기');
 await choose(page,'네, 서울에 살아요');
 await page.getByLabel('만 나이',{exact:true}).fill('24');
 await page.getByRole('button',{name:'다음',exact:true}).click();
 await expect(page.locator('.policy-choice')).toHaveCount(6);
}
async function basket(page){
 await page.locator('.policy-choice').filter({hasText:'청년 활동지원금'}).click();
 await page.getByRole('button',{name:'1개 담기',exact:true}).click();
 await expect(page.locator('#detail-dialog')).toBeVisible();
}
async function capture(page,name){
 mkdirSync('browser-artifacts/screens',{recursive:true});
 await page.screenshot({path:`browser-artifacts/screens/${name}.png`,fullPage:true});
}
test('basic journey, optional detail pause/resume, basket and consultation document',async({page,context})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.getByRole('heading',{level:1})).toContainText('요즘');
 const title=await page.locator('#page-title').boundingBox();
 expect(Math.abs(title.x+title.width/2-195)).toBeLessThan(5);
 await capture(page,'01-situation');
 await basic(page);await capture(page,'04-directions');await basket(page);
 await page.getByRole('button',{name:'더 자세히 확인하기',exact:true}).click();
 await choose(page,'혼자 살아요');
 await page.getByRole('button',{name:'상세 확인 잠시 멈추기',exact:true}).click();
 await page.getByRole('button',{name:'상세 확인 이어가기',exact:true}).click();
 await choose(page,'지금은 취업하지 않았어요');
 await choose(page,'저녁·주말이 편해요');
 await expect(page.getByRole('button',{name:'담은 지원 준비하기',exact:true})).toBeVisible();
 await capture(page,'07-updated');
 await page.getByRole('button',{name:'담은 지원 준비하기',exact:true}).click();
 await expect(page.getByRole('checkbox')).toHaveCount(3);
 await page.getByRole('checkbox',{name:'신청 기간 확인하기 완료 표시',exact:true}).check();
 await expect(page.getByRole('heading',{level:1})).toContainText('2개');
 await capture(page,'08-preparation');
 await page.getByRole('button',{name:'상담 요약서',exact:true}).click();
 await expect(page.locator('.document')).toContainText('만 24세');
 await expect(page.locator('.document')).toContainText('가상 예시');
 await expect(page.locator('.document')).toContainText('선호 · 자격에 사용 안 함');
 await context.grantPermissions(['clipboard-read','clipboard-write']);
 await page.getByRole('button',{name:'복사하기',exact:true}).click();
 await expect(page.locator('#toast')).toContainText('복사했어요');
 expect(await page.evaluate(()=>navigator.clipboard.readText())).toContain('만 24세');
 await capture(page,'09-consultation');
 await page.pdf({path:'browser-artifacts/screens/09-consultation.pdf',format:'A4',printBackground:true});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 expect(errors).toEqual([]);
});
test('unknown and skip keep missing-input conditions and official references',async({page})=>{
 await page.goto('/');
 for(let i=0;i<4;i++)await page.getByRole('button',{name:'답하지 않고 넘어가기',exact:true}).click();
 await expect(page.locator('.policy-choice')).toHaveCount(6);await basket(page);
 await page.getByRole('button',{name:'지금 결과로 볼게요',exact:true}).click();
 await page.getByText('조건별 확인사항과 근거',{exact:true}).first().click();
 await expect(page.locator('.condition-list').first()).toContainText('입력 부족');
 await page.getByRole('button',{name:'이용 안내',exact:true}).click();
 await page.getByRole('button',{name:'공식 정책 참고자료 보기',exact:true}).click();
 await expect(page.locator('.official-item')).toHaveCount(6);
 await expect(page.locator('#official-list')).toContainText('종료됐습니다');
});
test('declining detail preserves selected support and leads to preparation',async({page})=>{
 await basic(page);await basket(page);
 await page.getByRole('button',{name:'지금 결과로 볼게요',exact:true}).click();
 await expect(page.locator('.policy-choice')).toHaveCount(6);
 await page.getByRole('button',{name:'담은 지원 준비하기',exact:true}).click();
 await expect(page.getByRole('heading',{level:1})).toContainText('3개');
 await expect(page.getByRole('button',{name:'실제 공식 정책 참고자료 보기',exact:true})).toBeVisible();
});
test('age correction removes mismatch from candidates and basket; unknown restores it',async({page})=>{
 await basic(page);await basket(page);
 await page.getByRole('button',{name:'지금 결과로 볼게요',exact:true}).click();
 await page.getByRole('button',{name:'내 답변 수정',exact:true}).click();
 await page.locator('#edit-key').selectOption('age');await page.locator('#edit-value').fill('37');
 await page.getByRole('button',{name:'수정 반영하기',exact:true}).click();
 const candidate=page.locator('.policy-choice').filter({hasText:'청년 활동지원금'});
 await expect(candidate).toBeDisabled();await expect(page.locator('#basket-button')).toBeHidden();
 await page.getByRole('button',{name:'내 답변 수정',exact:true}).click();
 await page.locator('#edit-key').selectOption('age');await page.locator('#edit-unknown').check();
 await page.getByRole('button',{name:'수정 반영하기',exact:true}).click();
 await expect(candidate).toBeEnabled();await expect(page.locator('.policy-choice:not(.excluded)')).toHaveCount(6);
});
test('empty and data-error screens are recoverable without losing previous answers',async({page})=>{
 await basic(page);await page.getByRole('button',{name:'이용 안내',exact:true}).click();
 await page.locator('#scenario').selectOption('empty');await page.locator('#help-close').click();
 await page.getByRole('button',{name:'내 답변 수정',exact:true}).click();
 await page.locator('#edit-key').selectOption('age');await page.locator('#edit-value').fill('25');
 await page.getByRole('button',{name:'수정 반영하기',exact:true}).click();
 await expect(page.locator('.empty')).toBeVisible();await capture(page,'10-empty');
 await page.getByRole('button',{name:'이용 안내',exact:true}).click();
 await page.locator('#scenario').selectOption('error');await page.locator('#help-close').click();
 await page.getByRole('button',{name:'내 답변 수정',exact:true}).click();
 await page.locator('#edit-key').selectOption('age');await page.locator('#edit-value').fill('26');
 await page.getByRole('button',{name:'수정 반영하기',exact:true}).click();
 await expect(page.locator('#edit-error')).toBeVisible();await page.locator('#edit-close').click();
 await expect(page.locator('#chips')).toContainText('만 25세');
 await page.getByRole('button',{name:'이용 안내',exact:true}).click();
 await page.locator('#scenario').selectOption('normal');await page.locator('#help-close').click();
 await page.getByRole('button',{name:'다시 시도하기',exact:true}).click();
 await expect(page.locator('#chips')).toContainText('만 26세');
 await expect(page.locator('.policy-choice:not(.excluded)')).toHaveCount(6);
});
test('real FastAPI serves modules, accepts manual region correction and retains official guidance',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8765/demo');
 await expect(page.getByRole('heading',{level:1})).toContainText('요즘');
 await expect(page.locator('#demo-banner')).toBeHidden();
 await choose(page,'쉬고 있어요');await choose(page,'생활비 부담 줄이기');
 await page.getByLabel('만 나이',{exact:true}).fill('24');
 await page.getByRole('button',{name:'다음',exact:true}).click();
 await page.getByLabel('실제 거주 지역',{exact:true}).selectOption('__manual__');
 await page.getByLabel('실제 거주 지역 5자리 코드',{exact:true}).fill('11680');
 await page.getByRole('button',{name:'다음',exact:true}).click();
 await expect(page.locator('.policy-choice')).toHaveCount(1);
 await page.locator('.policy-choice').click();await page.getByRole('button',{name:'1개 담기',exact:true}).click();
 await page.getByRole('button',{name:'지금 결과로 볼게요',exact:true}).click();
 await page.getByRole('button',{name:'내 답변 수정',exact:true}).click();
 await page.locator('#edit-key').selectOption('region_code');
 await page.locator('#edit-value').selectOption('__manual__');await page.locator('#edit-manual').fill('11680');
 await page.getByRole('button',{name:'수정 반영하기',exact:true}).click();
 await page.getByText('조건별 확인사항과 근거',{exact:true}).click();
 await expect(page.getByRole('link',{name:'공식 공고 확인하기',exact:true})).toHaveAttribute('href','https://example.test/official');
 await page.getByRole('button',{name:'담은 지원 준비하기',exact:true}).click();
 await page.getByRole('button',{name:'상담 요약서',exact:true}).click();
 await expect(page.locator('.document')).toContainText('강남구');
 expect(errors).toEqual([]);
});
