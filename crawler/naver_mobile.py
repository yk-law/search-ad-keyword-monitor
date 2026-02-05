import urllib.parse

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from logo_detector import YKLogoDetector

from util import (
    is_brand_content,
    get_card_url,
    get_thumbnail_element_from_card,
    is_kin_content,
    resolve_ugc_content_type,
)
from config.constants import (
    NAVER_TARGET_KEYWORDS,
    NAVER_BRAND_CARD_SELECTOR,
    NAVER_PLACE_ROOT_SELECTOR,
    NAVER_PLACE_CARD_SELECTOR,
    NAVER_UGC_CARD_SELECTOR,
)

from ocr_util import extract_text_from_image_element


def ensure_naver_exact_query(driver, keyword: str, timeout: int = 5) -> bool:
    """
    '제안 검색어' 블록이 노출되면, 원래 keyword 링크를 클릭해
    정확한 검색 결과로 전환한다.
    """
    try:
        container = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.sp_nkeyword_suggest, div.sp_nkeyword")
            )
        )
    except Exception:
        return False

    try:
        links = container.find_elements(By.CSS_SELECTOR, "a[href*='query=']")
        target = next((a for a in links if a.text.strip() == keyword), None)
        if not target:
            return False

        target.click()

        q = urllib.parse.quote(keyword)
        try:
            WebDriverWait(driver, timeout).until(
                lambda d: f"query={q}" in d.current_url
            )
        except Exception:
            pass

        return True
    except Exception:
        return False


# ==============================
# NAVER: 파워링크
# ==============================
def find_naver_powerlink_rank(driver):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, "li.bx")
    rank = 0

    for card in cards:
        try:
            card.find_element(By.CSS_SELECTOR, "a[href*='ader.naver.com']")
        except Exception:
            continue

        rank += 1
        text = card.text.lower()
        matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]

        if matched:
            results.append(
                {
                    "section": "파워링크",
                    "rank": rank,
                    "matched_snippet": card.text.replace("\n", " ")[:200],
                }
            )

    return results


# ==============================
# NAVER: 브랜드콘텐츠
# ==============================
def find_naver_brand_content_rank(driver):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_BRAND_CARD_SELECTOR)

    for idx, card in enumerate(cards, start=1):
        text = card.text.lower()
        matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]

        if matched:
            results.append(
                {
                    "section": "브랜드콘텐츠",
                    "rank": idx,
                    "matched_snippet": card.text.replace("\n", " ")[:200],
                }
            )

    return results


# ==============================
# NAVER: 플레이스
# ==============================
def has_naver_place_block(driver) -> bool:
    try:
        driver.find_element(By.CSS_SELECTOR, NAVER_PLACE_ROOT_SELECTOR)
        return True
    except Exception:
        return False


def find_naver_place_rank(driver):
    results = []
    root = driver.find_element(By.CSS_SELECTOR, NAVER_PLACE_ROOT_SELECTOR)
    cards = root.find_elements(By.CSS_SELECTOR, NAVER_PLACE_CARD_SELECTOR)

    ad_rank = 0
    organic_rank = 0

    for card in cards:
        text = card.text.lower()
        is_ad = "광고" in text

        if is_ad:
            ad_rank += 1
            section = "플레이스_광고"
            rank = ad_rank
        else:
            organic_rank += 1
            section = "플레이스_일반"
            rank = organic_rank

        matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]
        if matched:
            results.append(
                {
                    "section": section,
                    "rank": rank,
                    "matched_snippet": card.text.replace("\n", " ")[:200],
                }
            )

    return results


# ==============================
# NAVER: 인기글 (UGC) / pHash 로고 검출
# ==============================
def find_popular_content(driver, logo_detector: YKLogoDetector):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_UGC_CARD_SELECTOR)
    popular_rank = 0

    for card in cards:
        if is_brand_content(card):
            continue

        url = get_card_url(card)

        if is_kin_content(url):
            continue

        text = card.text.lower()
        text_hit = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]

        img_el = get_thumbnail_element_from_card(card)
        logo_hit = False
        logo_info = None

        if img_el:
            status, template_name, distance = logo_detector.match(
                img_el.screenshot_as_png
            )
            if status in ("same", "similar"):
                logo_hit = True
                logo_info = {
                    "logo_match_type": status,
                    "template": template_name,
                    "phash_distance": int(distance),
                }

        if text_hit or logo_hit:
            popular_rank += 1
            results.append(
                {
                    "section": "인기글",
                    "content_type": resolve_ugc_content_type(url),
                    "rank": popular_rank,
                    "source_type": "ugc",
                    "url": url,
                    **(logo_info or {}),
                }
            )

    return results


# ==============================
# NAVER: 인기글 (UGC) / easyOCR 로고 검출
# ==============================
def find_popular_content_ocr(driver):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_UGC_CARD_SELECTOR)
    popular_rank = 0

    for card in cards:
        if is_brand_content(card):
            continue

        url = get_card_url(card)

        if is_kin_content(url):
            continue

        text = card.text.lower()
        text_hit = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]

        img_el = get_thumbnail_element_from_card(card)
        ocr_text = ""
        # img_src = img_el.get_attribute("src") if img_el else None
        # print(f"[OCR] card_url: {url}")
        # print(f"[OCR] img_src: {img_src}")

        if img_el:
            ocr_text = extract_text_from_image_element(img_el)
        # print(f"[OCR] extracted text: {ocr_text}")

        ocr_hit = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in ocr_text]

        if text_hit or ocr_hit:
            popular_rank += 1
            results.append(
                {
                    "section": "인기글",
                    "content_type": resolve_ugc_content_type(url),
                    "rank": popular_rank,
                    "source_type": "ugc",
                    "url": url,
                    "ocr_text": ocr_text[:200],
                }
            )

    return results
