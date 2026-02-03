import base64
import requests
import easyocr
from requests.exceptions import RequestException

ocr_reader = easyocr.Reader(["ko", "en"], gpu=False)


def _fetch_image_bytes(img_el) -> bytes | None:
    if img_el is None:
        return None

    src = img_el.get_attribute("src")
    if not src:
        return None

    try:
        resp = requests.get(src, timeout=(3, 5))
        resp.raise_for_status()
        return resp.content
    except requests.RequestException:
        return None


def extract_text_from_image_element(img_el) -> str:
    if img_el is None:
        return ""

    img_bytes = _fetch_image_bytes(img_el)
    if not img_bytes:
        return ""

    try:
        results = ocr_reader.readtext(img_bytes, detail=0)
        return " ".join(results)
    except Exception:
        return ""
