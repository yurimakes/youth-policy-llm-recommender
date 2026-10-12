"""공개 체험 빌드의 실행 모드·리소스 연결·배포 범위를 검증합니다."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_demo import build
from scripts.serve_demo import DemoHandler


class DemoBuildTests(unittest.TestCase):
    def test_preview_serves_every_built_javascript_module(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(output)
            server = ThreadingHTTPServer(("127.0.0.1", 0), partial(DemoHandler, directory=directory))
            worker = Thread(target=lambda: server.serve_forever(poll_interval=0.01), daemon=True)
            worker.start()
            try:
                for module in (output / "demo/assets").glob("*.mjs"):
                    with self.subTest(module=module.name):
                        url = f"http://127.0.0.1:{server.server_port}/demo/assets/{module.name}"
                        with urlopen(url, timeout=2) as response:
                            self.assertEqual(response.status, 200)
                            self.assertEqual(response.headers.get_content_type(), "text/javascript")
                            self.assertEqual(response.read(), module.read_bytes())
            finally:
                server.shutdown()
                server.server_close()
                worker.join(timeout=2)

    def test_static_copy_uses_mock_without_changing_local_api_html(self):
        source = Path(__file__).resolve().parents[1] / "demo" / "index.html"
        original = source.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(output)
            html = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn('data-runtime="mock"', html)
            self.assertEqual(html, (output / "demo/index.html").read_text(encoding="utf-8"))
            for resource in re.findall(r'(?:src|href)="(/demo/assets/[^\"]+)"', html):
                self.assertTrue((output / resource.lstrip("/")).is_file(), resource)
        self.assertEqual(source.read_text(encoding="utf-8"), original)
        self.assertIn('data-runtime="api"', original)

    def test_build_contains_only_public_ui_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            build(output)
            names = {str(p.relative_to(output)).replace("\\", "/") for p in output.rglob("*") if p.is_file()}
            self.assertEqual(names, {"index.html", "demo/index.html", "demo/assets/style.css",
                                     "demo/assets/app.mjs", "demo/assets/client.mjs", "demo/assets/mock.mjs", "demo/assets/preparation.mjs",
                                     "demo/assets/official-policies.json", "demo/assets/Pretendard-Regular.woff2",
                                     "demo/assets/Pretendard-SemiBold.woff2", "demo/assets/Pretendard-ExtraBold.woff2",
                                     "demo/assets/Pretendard-OFL.txt"})


if __name__ == "__main__":
    unittest.main()
