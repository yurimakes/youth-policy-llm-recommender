"""단순한 장바구니 도형으로 설치용 PNG 아이콘을 재현합니다. 서버 실행에는 필요 없습니다."""

from pathlib import Path


def build_icons(destination: Path) -> None:
    """Pillow가 있는 개발 환경에서 192·512·180px 아이콘을 생성합니다."""
    from PIL import Image, ImageDraw

    size = 2048
    image = Image.new("RGB", (size, size), "#3182f6")
    draw = ImageDraw.Draw(image)
    point = lambda x, y: (round(x * size), round(y * size))
    draw.line([point(.38, .44), point(.43, .30), point(.57, .30), point(.62, .44)],
              fill="white", width=round(.035 * size), joint="curve")
    draw.polygon([point(.27, .43), point(.73, .43), point(.68, .70), point(.32, .70)], fill="white")
    draw.line([point(.42, .56), point(.48, .62), point(.60, .50)], fill="#3182f6",
              width=round(.035 * size), joint="curve")
    destination.mkdir(parents=True, exist_ok=True)
    for filename, pixels in (("app-icon-192.png", 192), ("app-icon-512.png", 512), ("apple-touch-icon.png", 180)):
        image.resize((pixels, pixels), Image.Resampling.LANCZOS).save(destination / filename)


if __name__ == "__main__":
    build_icons(Path(__file__).resolve().parents[1] / "demo")
