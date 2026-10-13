// Installation and connectivity never read, store or send intake state.
export function setupPwa({window: win = window, navigator: nav = navigator, document: doc = document} = {}) {
  const install = doc.getElementById('install-app');
  const guide = doc.getElementById('install-guide');
  const update = doc.getElementById('apply-update');
  const connection = doc.getElementById('connection-note');
  let prompt = null, waiting = null, reloadRequested = false;
  const standalone = () => win.matchMedia('(display-mode: standalone)').matches || nav.standalone === true;
  const installed = () => {
    if (!standalone()) return;
    install.hidden = true;
    guide.textContent = '홈 화면 앱으로 이용 중이에요. 입력은 이 화면에서만 유지돼요.';
  };
  const connectivity = () => {
    connection.hidden = nav.onLine !== false;
    connection.textContent = '인터넷 연결이 끊겼어요. 현재 답변은 이 화면에 유지돼요. 연결 후 다시 시도해 주세요. 새로고침하면 초기화돼요.';
  };
  installed(); connectivity();
  win.addEventListener('offline', connectivity);
  win.addEventListener('online', connectivity);
  win.addEventListener('beforeinstallprompt', event => {
    event.preventDefault(); prompt = event;
    if (!standalone()) install.hidden = false;
  });
  win.addEventListener('appinstalled', () => {
    prompt = null; install.hidden = true;
    guide.textContent = '홈 화면에 추가했어요. 정책 안내에는 인터넷 연결이 필요해요.';
  });
  install.addEventListener('click', async () => {
    if (!prompt) return;
    const current = prompt; prompt = null; install.hidden = true;
    try { await current.prompt(); await current.userChoice; }
    catch { guide.textContent = '브라우저 메뉴에서 홈 화면에 추가할 수 있어요.'; }
  });
  update.addEventListener('click', () => {
    if (!waiting || !win.confirm('새 버전을 열면 입력한 답변과 담은 지원이 초기화돼요. 지금 새 버전을 열까요?')) return;
    reloadRequested = true; update.disabled = true;
    waiting.postMessage({type:'APPLY_UPDATE'});
  });
  if (!win.isSecureContext || !('serviceWorker' in nav)) return;
  nav.serviceWorker.addEventListener('controllerchange', () => {
    if (reloadRequested) win.location.reload();
  });
  const showUpdate = worker => {
    if (!worker || !nav.serviceWorker.controller) return;
    waiting = worker; update.hidden = false;
  };
  nav.serviceWorker.register('/sw.js', {scope:'/', updateViaCache:'none'}).then(registration => {
    showUpdate(registration.waiting);
    registration.addEventListener('updatefound', () => {
      const worker = registration.installing;
      worker?.addEventListener('statechange', () => {
        if (worker.state === 'installed') showUpdate(registration.waiting);
      });
    });
  }).catch(() => {
    guide.textContent = '설치 안내를 준비하지 못했어요. 일반 브라우저에서 계속 이용할 수 있어요.';
  });
}
