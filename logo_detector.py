from pathlib import Path
from PIL import Image
import imagehash
import io


class YKLogoDetector:
    def __init__(self, template_dir: str):
        self.templates = []

        # print(f"[PHASH] loading templates from: {template_dir}")

        for p in Path(template_dir).iterdir():
            if p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue

            img = Image.open(p).convert("RGB")
            h = imagehash.phash(img)
            self.templates.append((p.name, h))

            # print(f"[PHASH][OK] {p.name} loaded")

        if not self.templates:
            raise ValueError("pHash 템플릿을 하나도 로드하지 못했습니다.")

        # print(f"[PHASH] total templates loaded = {len(self.templates)}")

    def match(self, img_bytes: bytes) -> tuple[str, str | None, int]:
        target_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        target_hash = imagehash.phash(target_img)

        best_dist = 999
        best_name = None

        for name, tmpl_hash in self.templates:
            dist = int(target_hash - tmpl_hash)  # Hamming distance

            if dist < best_dist:
                best_dist = dist
                best_name = name

        # 🔴 CHANGED: 거리 구간 분류
        if best_dist <= 5:
            status = "same"
        elif best_dist <= 14:
            status = "similar"
        else:
            status = "different"

        # print(f"[PHASH][RESULT] status={status} template={best_name} dist={best_dist}")

        return status, best_name, best_dist
