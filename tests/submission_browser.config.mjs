import {defineConfig} from '@playwright/test';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const python=process.env.TEST_PYTHON||'.venv/bin/python';
const directory=process.env.TEST_DEMO_DIR||'submission-demo';
export default defineConfig({
 testDir:'.',testMatch:'test_submission_browser.spec.mjs',workers:1,timeout:45000,
 reporter:'list',outputDir:fileURLToPath(new URL('../browser-artifacts/traces',import.meta.url)),
 use:{baseURL:'http://127.0.0.1:8766',viewport:{width:390,height:844},trace:'retain-on-failure'},
 webServer:[
  {command:`"${python}" scripts/serve_submission_demo.py --port 8766 --directory "${directory}"`,cwd:root,url:'http://127.0.0.1:8766',timeout:30000},
  {command:`"${python}" tests/serve_demo_fixture.py`,cwd:root,url:'http://127.0.0.1:8765/health',timeout:30000}
 ]
});
