import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {setupPwa} from '../demo/pwa.mjs';

const source=readFileSync(new URL('../demo/sw.js',import.meta.url),'utf8');
function worker(fetcher, names=['unrelated-cache']) {
 const listeners={}, stores=new Map(names.map(name=>[name,new Map()]));let skipped=0,claimed=0;
 const cacheApi={keys:async()=>[...stores.keys()],delete:async key=>stores.delete(key),open:async key=>{
  if(!stores.has(key))stores.set(key,new Map());const entries=stores.get(key);
  return {put:async(key,value)=>entries.set(key,value),match:async key=>entries.get(key)};
 }};
 const self={location:{origin:'https://app.example.test'},clients:{claim:async()=>{claimed++;}},
  skipWaiting:async()=>{skipped++;},addEventListener:(name,fn)=>listeners[name]=fn};
 runInNewContext(source,{self,caches:cacheApi,fetch:fetcher,URL,Response,Set,Promise,Error});
 return {stores,get skipped(){return skipped;},get claimed(){return claimed;},
  dispatch:(name,values={})=>{let result;listeners[name]({...values,waitUntil:p=>result=p,respondWith:p=>result=p});return result;}};
}
const notice=()=>new Response('<body data-offline-page="jiwon-basket">connection only</body>',{headers:{'Content-Type':'text/html'}});
const navigation={url:'https://app.example.test/demo/',method:'GET',mode:'navigate'};

test('worker stores only the fixed offline notice and never activates updates automatically',async()=>{
 const calls=[];const w=worker(async(url,options)=>{calls.push({url,options});return notice();});
 await w.dispatch('install');assert.equal(w.skipped,0);
 assert.equal(calls[0].url,'/offline.html');assert.equal(calls[0].options.cache,'no-store');
 assert.equal(calls[0].options.credentials,'omit');
 assert.deepEqual([...w.stores.get('jiwon-basket-offline-v1').keys()],['/offline.html']);
 await w.dispatch('message',{data:{type:'OTHER'}});assert.equal(w.skipped,0);
 await w.dispatch('message',{data:{type:'APPLY_UPDATE'}});assert.equal(w.skipped,1);
});

test('failed or unexpected notice is not saved as an offline page',async()=>{
 for(const response of [new Response('private response',{status:503}),new Response('private API body',{headers:{'Content-Type':'application/json'}}),new Response('policy HTML',{headers:{'Content-Type':'text/html'}})]){
  const w=worker(async()=>response);await assert.rejects(w.dispatch('install'));
  assert.equal(w.stores.has('jiwon-basket-offline-v1'),false);
 }
});

test('activation removes only older app notice caches',async()=>{
 const w=worker(async()=>notice(),['unrelated-cache','jiwon-basket-offline-v0','jiwon-basket-offline-v1']);
 await w.dispatch('activate');assert.deepEqual([...w.stores.keys()],['unrelated-cache','jiwon-basket-offline-v1']);assert.equal(w.claimed,1);
});

test('API calls, assets, cross-origin and other navigations are never intercepted',()=>{
 let calls=0;const w=worker(async()=>{calls++;return notice();});
 for(const request of [{...navigation,method:'POST'}, {...navigation,mode:'cors',url:'https://app.example.test/api/v1/intake/explanation'},
  {...navigation,url:'https://app.example.test/api/v1/intake/start'}, {...navigation,url:'https://app.example.test/demo/assets/official-policies.json'},
  {...navigation,url:'https://other.example.test/demo/'}, {...navigation,url:'https://app.example.test/private'}]){
  assert.equal(w.dispatch('fetch',{request}),undefined);
 }
 assert.equal(calls,0);
});

test('online server errors are preserved and are not cached or replaced with offline advice',async()=>{
 const failed=new Response('server unavailable',{status:503});const w=worker(async()=>failed);
 assert.equal(await w.dispatch('fetch',{request:navigation}),failed);assert.equal(w.stores.size,1);
});

test('offline navigation returns the notice without caching successful app pages',async()=>{
 let offline=false;
 const w=worker(async(url,options)=>{
  if(url==='/offline.html')return notice();assert.equal(options.cache,'no-store');
  if(offline)throw new TypeError('offline');return new Response('app with PRIVATE-MARKER');
 });
 await w.dispatch('install');await w.dispatch('fetch',{request:navigation});offline=true;
 const response=await w.dispatch('fetch',{request:navigation});assert.match(await response.text(),/connection only/);
 assert.deepEqual([...w.stores.get('jiwon-basket-offline-v1').keys()],['/offline.html']);
});

function ui({secure=true,standalone=false,confirm=false}={}){
 const elements=Object.fromEntries(['install-app','install-guide','apply-update','connection-note'].map(id=>{
  const element=new EventTarget();Object.assign(element,{hidden:true,textContent:'manual installation guide',disabled:false});return [id,element];
 }));
 const waiting={messages:[],postMessage(message){this.messages.push(message);}};
 const registration=new EventTarget();registration.waiting=waiting;
 const serviceWorker=new EventTarget();serviceWorker.controller={};const registrations=[];
 serviceWorker.register=async(...args)=>{registrations.push(args);return registration;};
 const nav={onLine:true,serviceWorker};let reloads=0;
 const win=new EventTarget();Object.assign(win,{isSecureContext:secure,matchMedia:()=>({matches:standalone}),confirm:()=>confirm,location:{reload:()=>reloads++}});
 setupPwa({window:win,navigator:nav,document:{getElementById:id=>elements[id]}});
 return {elements,nav,win,waiting,registrations,get reloads(){return reloads;}};
}

test('installation is an explicit action and connectivity does not reload or store state',async()=>{
 const fixture=ui();await new Promise(resolve=>setImmediate(resolve));
 let prompted=0;const event=new Event('beforeinstallprompt',{cancelable:true});
 Object.assign(event,{prompt:async()=>prompted++,userChoice:Promise.resolve({outcome:'dismissed'})});fixture.win.dispatchEvent(event);
 assert.equal(event.defaultPrevented,true);assert.equal(prompted,0);assert.equal(fixture.elements['install-app'].hidden,false);
 fixture.elements['install-app'].dispatchEvent(new Event('click'));await new Promise(resolve=>setImmediate(resolve));assert.equal(prompted,1);
 fixture.nav.onLine=false;fixture.win.dispatchEvent(new Event('offline'));
 assert.equal(fixture.elements['connection-note'].hidden,false);assert.match(fixture.elements['connection-note'].textContent,/현재 답변/);
 fixture.nav.onLine=true;fixture.win.dispatchEvent(new Event('online'));assert.equal(fixture.elements['connection-note'].hidden,true);
 assert.equal(fixture.reloads,0);assert.equal(fixture.registrations[0][0],'/sw.js');
});

test('updates reload only after explicit confirmation; cancellation keeps the current flow',async()=>{
 for(const confirm of [false,true]){
  const fixture=ui({confirm});await new Promise(resolve=>setImmediate(resolve));
  assert.equal(fixture.elements['apply-update'].hidden,false);
  fixture.nav.serviceWorker.dispatchEvent(new Event('controllerchange'));assert.equal(fixture.reloads,0);
  fixture.elements['apply-update'].dispatchEvent(new Event('click'));
  assert.equal(fixture.waiting.messages.length,confirm?1:0);
  fixture.nav.serviceWorker.dispatchEvent(new Event('controllerchange'));assert.equal(fixture.reloads,confirm?1:0);
 }
});

test('unsupported contexts keep ordinary browsing and standalone hides install controls',async()=>{
 const insecure=ui({secure:false});assert.equal(insecure.registrations.length,0);
 const installed=ui({standalone:true});assert.equal(installed.elements['install-app'].hidden,true);assert.match(installed.elements['install-guide'].textContent,/이용 중/);
});
