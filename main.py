from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import urllib.parse
import json
from datetime import datetime, timezone
from pathlib import Path

from logo_detector import YKLogoDetector


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
    "YK",
    "법무법인YK",
    "법무법인 YK",
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
    return "https://m.search.naver.com/search.naver?query=" + urllib.parse.quote(
        keyword
    )


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()


def get_thumbnail_element_from_card(card):
    try:
        return card.find_element(
            By.CSS_SELECTOR,
            "div[data-sds-comp='RectangleImage']:not(.sds-comps-image-circle) img",
        )
    except Exception:
        return None


def get_card_url(card):
    # 1️⃣ 게시글 링크 (쿼리스트링 포함) 최우선
    try:
        a = card.find_element(By.CSS_SELECTOR, "a[data-heatmap-target='.link'][href]")
        return a.get_attribute("href")
    except Exception:
        pass

    # 2️⃣ fallback: 게시글 ID 패턴
    try:
        a = card.find_element(By.CSS_SELECTOR, "a[href*='/'][href*='?art=']")
        return a.get_attribute("href")
    except Exception:
        pass

    # 3️⃣ 최후 fallback
    try:
        a = card.find_element(By.CSS_SELECTOR, "a[href]")
        return a.get_attribute("href")
    except Exception:
        return None


def save_element_screenshot(element, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    element.screenshot(path)


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
        text = card.text.lower()
        matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]

        if matched:
            results.append(
                {
                    "section": "powerlink",
                    "rank": ad_rank,
                    "matched_keywords": matched,
                    "matched_snippet": card.text.replace("\n", " ")[:200],
                }
            )

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
                text = card.text.lower()
                matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]
                if matched:
                    results.append(
                        {
                            "section": "brand",
                            "rank": idx,
                            "matched_keywords": matched,
                            "matched_snippet": card.text.replace("\n", " ")[:200],
                        }
                    )
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

        matched = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]
        if matched:
            results.append(
                {
                    "section": section,
                    "rank": rank,
                    "matched_keywords": matched,
                    "matched_snippet": card.text.replace("\n", " ")[:200],
                }
            )

    return results


# ==============================
# NAVER: UGC + 로고 검출
# ==============================


def find_ugc_with_logo(driver, logo_detector: YKLogoDetector):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_UGC_CARD_SELECTOR)

    # print(f"[UGC] total cards found = {len(cards)}")

    for idx, card in enumerate(cards, start=1):
        # 카드 자체 스크린샷
        # save_element_screenshot(
        #     card,
        #     f"debug/ugc_cards/card_{idx}.png",
        # )

        text = card.text.lower()
        url = get_card_url(card)

        text_hit = [kw for kw in NAVER_TARGET_KEYWORDS if kw.lower() in text]
        # print(f"[UGC][{idx}] text_hit={bool(text_hit)} url={url}")

        if text_hit:
            results.append(
                {
                    "section": "ugc_text",
                    # "rank": idx,
                    "matched_keywords": text_hit,
                    "matched_snippet": card.text.replace("\n", " ")[:200],
                    "url": url,
                }
            )
            continue

        img_el = get_thumbnail_element_from_card(card)
        if not img_el:
            print(f"[UGC][{idx}] ❌ no img element")
            continue

        # 썸네일만 따로 스크린샷
        # save_element_screenshot(
        #     img_el,
        #     f"debug/ugc_thumbnails/thumb_{idx}.png",
        # )

        status, template_name, distance = logo_detector.match(img_el.screenshot_as_png)

        # print(
        #     f"[PHASH][{idx}] status={status} template={template_name} "
        #     f"distance={distance} url={url}"
        # )

        # 🔴 핵심 변경 지점
        if status in ("same", "similar"):
            results.append(
                {
                    "section": "ugc_logo",
                    # "rank": idx,
                    "logo_match_type": status,  # same / similar
                    "template": template_name,
                    "phash_distance": distance,
                    "url": url,
                }
            )

    return results


# ==============================
# main
# ==============================


def main():
    crawler = BaseCrawler()
    keywords = load_keywords()

    logo_detector = YKLogoDetector(template_dir="assets/naver_thumbnails")

    index_name = f"search_ad_keyword_monitoring-{datetime.now(timezone.utc):%Y-%m-%d}"

    try:
        for idx, keyword in enumerate(keywords, start=1):
            print(f"\n[{idx}] keyword='{keyword}'")

            crawler.open(build_naver_mobile_search_url(keyword))
            time.sleep(4)

            ts = now_utc_iso()
            bulk_docs = []

            # 1. 파워링크
            for r in find_naver_powerlink_rank(crawler.driver):
                r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                bulk_docs.append(r)

            # 2. 브랜드 콘텐츠
            for r in find_naver_brand_content_rank(crawler.driver):
                r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                bulk_docs.append(r)

            # 3. 플레이스
            if has_naver_place_block(crawler.driver):
                for r in find_naver_place_rank(crawler.driver):
                    r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                    bulk_docs.append(r)

            # 4. UGC + 로고 (항상 탐색)
            for r in find_ugc_with_logo(crawler.driver, logo_detector):
                r.update({"source": "naver", "query": keyword, "@timestamp": ts})
                bulk_docs.append(r)

            if bulk_docs:
                print(
                    f"[ES MOCK] index={index_name}\n"
                    f"{json.dumps(bulk_docs, ensure_ascii=False, indent=2)}"
                )

    finally:
        crawler.close()


if __name__ == "__main__":
    main()
