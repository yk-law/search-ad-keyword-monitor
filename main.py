from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import urllib.parse
import json
from datetime import datetime, timezone

from ocr import extract_text_from_image_bytes, has_yk_from_ocr


# ==============================
# BaseCrawler
# ==============================

class BaseCrawler:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.binary_location = "/snap/bin/chromium"
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--disable-software-rasterizer")
        self.driver = webdriver.Chrome(options=options)

    def open(self, url: str):
        self.driver.get(url)

    def close(self):
        self.driver.quit()


# ==============================
# NAVER 설정
# ==============================

NAVER_TARGET_KEYWORDS = [
    "yk",
    "법무법인yk",
    "법무법인 yk",
]

NAVER_BRAND_CARD_SELECTOR = "div._fe_view_power_content[data-template-id='ugcItem']"
NAVER_PLACE_ROOT_SELECTOR = "#place-app-root"
NAVER_PLACE_CARD_SELECTOR = "li"
NAVER_UGC_CARD_SELECTOR = "div[data-template-id='ugcItem']"


# ==============================
# Util
# ==============================

def load_keywords():
    with open("config/keywords.json", encoding="utf-8") as f:
        return json.load(f)["keywords"]

def build_naver_mobile_search_url(keyword: str) -> str:
    return "https://m.search.naver.com/search.naver?query=" + urllib.parse.quote(keyword)

def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()

def find_matched_keywords_and_snippet(card):
    text = card.text.lower()
    matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw in text]

    if not matched:
        return None, None

    snippet = card.text.replace("\n", " ")[:200]
    return matched, snippet


def get_thumbnail_element_from_card(card):
    try:
        return card.find_element(By.CSS_SELECTOR, "img")
    except Exception:
        return None


# ==============================
# NAVER: 파워링크
# ==============================

def find_naver_powerlink_rank(driver):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, "li.bx")

    ad_rank = 0

    for card in cards:
        try:
            card.find_element(By.CSS_SELECTOR, "a[href*='ader.naver.com']")
        except Exception:
            continue

        ad_rank += 1

        matched, snippet = find_matched_keywords_and_snippet(card)
        if matched:
            results.append({
                "section": "powerlink",
                "rank": ad_rank,
                "matched_keywords": matched,
                "matched_snippet": snippet,
            })

    return results


# ==============================
# NAVER: 브랜드 콘텐츠
# ==============================

def find_naver_brand_content_rank(driver):
    results = []
    blocks = driver.find_elements(By.CSS_SELECTOR, "div[id^='fdr-']")

    for block in blocks:
        if "브랜드 콘텐츠" in block.text:
            cards = block.find_elements(By.CSS_SELECTOR, NAVER_BRAND_CARD_SELECTOR)
            for idx, card in enumerate(cards, start=1):
                matched, snippet = find_matched_keywords_and_snippet(card)
                if matched:
                    results.append({
                        "section": "brand",
                        "rank": idx,
                        "matched_keywords": matched,
                        "matched_snippet": snippet,
                    })
            break

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
            section = "place_ad"
            rank = ad_rank
        else:
            organic_rank += 1
            section = "place_organic"
            rank = organic_rank

        matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw in text]
        if matched:
            results.append({
                "section": section,
                "rank": rank,
                "matched_keywords": matched,
                "matched_snippet": card.text.replace("\n", " ")[:200],
            })

    return results


# ==============================
# NAVER: 타이틀 없는 UGC + OCR (스크린샷 기반)
# ==============================

def find_ugc_with_ocr(driver):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_UGC_CARD_SELECTOR)

    for idx, card in enumerate(cards, start=1):
        text = card.text.lower()

        if any(kw in text for kw in NAVER_TARGET_KEYWORDS):
            continue

        img_el = get_thumbnail_element_from_card(card)
        if not img_el:
            continue

        img_bytes = img_el.screenshot_as_png
        ocr_text = extract_text_from_image_bytes(img_bytes)

        # 🔴 반드시 추가
        print(f"[OCR][{idx}] raw='{ocr_text}'")

        if has_yk_from_ocr(ocr_text):
            print(f"[OCR MATCH][{idx}] normalized=YK")
            results.append({
                "section": "ugc_ocr",
                "rank": idx,
                "matched_keywords": ["yk"],
                "matched_snippet": ocr_text[:200],
            })

    return results


# ==============================
# Elasticsearch (MOCK)
# ==============================

def es_bulk_index(index: str, documents: list) -> int:
    if not documents:
        return 0

    print(f"\n[ES MOCK] index = {index}")
    for i, doc in enumerate(documents, start=1):
        print(f"  ({i}) {json.dumps(doc, ensure_ascii=False)}")

    return len(documents)


# ==============================
# main
# ==============================

def main():
    crawler = BaseCrawler()
    keywords = load_keywords()

    index_name = f"search_ad_keyword_monitoring-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"

    try:
        for idx, keyword in enumerate(keywords, start=1):
            print(f"\n[{idx}] keyword='{keyword}'")

            crawler.open(build_naver_mobile_search_url(keyword))
            time.sleep(4)

            ts = now_utc_iso()
            bulk_docs = []

            for r in find_naver_powerlink_rank(crawler.driver):
                r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                bulk_docs.append(r)

            for r in find_naver_brand_content_rank(crawler.driver):
                r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                bulk_docs.append(r)

            if has_naver_place_block(crawler.driver):
                for r in find_naver_place_rank(crawler.driver):
                    r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                    bulk_docs.append(r)

            # 🔴 최종 보루: OCR
            if not bulk_docs:
                for r in find_ugc_with_ocr(crawler.driver):
                    r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                    bulk_docs.append(r)

            if bulk_docs:
                es_bulk_index(index_name, bulk_docs)

    finally:
        crawler.close()


if __name__ == "__main__":
    main()
