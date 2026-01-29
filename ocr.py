# ocr.py
import pytesseract
from PIL import Image, ImageOps
from io import BytesIO
import re


def preprocess_for_logo(img: Image.Image) -> Image.Image:
    """
    로고 / 썸네일 전용 전처리
    """
    # 1. 그레이스케일
    img = img.convert("L")

    # 2. 대비 극대화
    img = ImageOps.autocontrast(img)

    # 3. 이진화 (threshold)
    img = img.point(lambda x: 0 if x < 160 else 255, "1")

    # 4. 확대 (OCR 인식률 향상)
    img = img.resize((img.width * 2, img.height * 2))

    return img


def extract_text_from_image_bytes(img_bytes: bytes) -> str | None:
    try:
        img = Image.open(BytesIO(img_bytes))
        img = preprocess_for_logo(img)

        text = pytesseract.image_to_string(
            img,
            lang="eng",
            config=(
                "--oem 1 "
                "--psm 7"   # 🔴 단일 텍스트 라인
            ),
        )

        return text.strip()

    except Exception as e:
        print(f"      [OCR ERROR] {e}")
        return None


def normalize_ocr_text(text: str) -> str:
    """
    OCR 노이즈 제거 (대문자만)
    """
    return re.sub(r"[^A-Z]", "", text.upper())


def has_yk_from_ocr(text: str) -> bool:
    if not text:
        return False

    normalized = normalize_ocr_text(text)

    # 🔴 YK / Y.K / Y-K 등 허용
    return "YK" in normalized
