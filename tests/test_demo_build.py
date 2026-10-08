"""공개 체험 빌드의 실행 모드·리소스 연결·배포 범위를 검증합니다."""
from pathlib import Path
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_demo import build


class DemoBuildTests(unittest.TestCase):
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
                                     "demo/assets/app.mjs", "demo/assets/client.mjs", "demo/assets/mock.mjs",
                                     "demo/assets/official-policies.json", "demo/assets/Pretendard-Regular.woff2",
                                     "demo/assets/Pretendard-SemiBold.woff2", "demo/assets/Pretendard-ExtraBold.woff2",
                                     "demo/assets/Pretendard-OFL.txt"})


if __name__ == "__main__":
    unittest.main()
