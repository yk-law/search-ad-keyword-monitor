from selenium import webdriver
from selenium.webdriver.common.by import By
import time, random
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
NAVER_UGC_CARD_SELECTOR = "div[data-template-id='ugcItem']"
NAVER_PLACE_ROOT_SELECTOR = "#place-app-root"
NAVER_PLACE_CARD_SELECTOR = "li"


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


def save_element_screenshot(element, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    element.screenshot(path)


def get_thumbnail_element_from_card(card):
    try:
        return card.find_element(
            By.CSS_SELECTOR,
            "div[data-sds-comp='RectangleImage']:not(.sds-comps-image-circle) img",
        )
    except Exception:
        return None


def get_card_url(card):
    # 1️⃣ heatmap link
    try:
        a = card.find_element(By.CSS_SELECTOR, "a[data-heatmap-target='.link'][href]")
        return a.get_attribute("href")
    except Exception:
        pass

    # 2️⃣ cafe fallback
    try:
        a = card.find_element(By.CSS_SELECTOR, "a[href*='?art=']")
        return a.get_attribute("href")
    except Exception:
        pass

    # 3️⃣ 최후 fallback
    try:
        a = card.find_element(By.CSS_SELECTOR, "a[href]")
        return a.get_attribute("href")
    except Exception:
        return None


def is_brand_content(card) -> bool:
    # ader 링크 기반
    try:
        card.find_element(By.CSS_SELECTOR, "a[href*='ader.naver.com']")
        return True
    except Exception:
        pass

    # 내부 플래그 기반
    cls = card.get_attribute("class") or ""
    return "_fe_view_power_content" in cls


def resolve_ugc_content_type(url: str) -> str:
    if not url:
        return url

    if "m.cafe.naver.com" in url:
        return "카페"

    if "m.blog.naver.com" in url:
        return "블로그"

    return url


# 지식인 여부 판단
def is_kin_content(url: str) -> bool:
    if not url:
        return False

    return "m.kin.naver.com" in url or "kin.naver.com" in url


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
# NAVER: 인기글 (순수 UGC)
# ==============================


def find_popular_content(driver, logo_detector: YKLogoDetector):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_UGC_CARD_SELECTOR)

    popular_rank = 0  # 인기글 전용 랭크 카운터

    for card in cards:
        # 1️⃣ 브랜드콘텐츠 제외
        if is_brand_content(card):
            continue

        url = get_card_url(card)

        # 2️⃣ 지식인 제외
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

        # 3️⃣ 텍스트 or 로고 매칭 시에만 랭킹 증가
        if text_hit or logo_hit:
            popular_rank += 1  #  여기서만 증가

            content_type = resolve_ugc_content_type(url)

            results.append(
                {
                    "section": "인기글",
                    "content_type": content_type,
                    "rank": popular_rank,  # 실제 인기글 내 순위
                    "source_type": "ugc",
                    "detect_reason": "text" if text_hit else "logo",
                    "url": url,
                    **(logo_info or {}),
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
            print(f"[{idx}] keyword='{keyword}'")

            crawler.open(build_naver_mobile_search_url(keyword))
            time.sleep(random.uniform(4.0, 6.0))

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

            for r in find_popular_content(crawler.driver, logo_detector):
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
