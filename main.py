from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import urllib.parse
import json
from datetime import datetime, timezone
from elasticsearch import Elasticsearch, helpers


# ==============================
# BaseCrawler (공통)
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
    "YK",
    "법무법인YK",
    "법무법인 YK",
    "yk",
    "법무법인yk",
    "법무법인 yk",
]

NAVER_POWERLINK_CARD_SELECTOR = "div[id^='mobilePowerLink_'] ul#power_link_body > li"
NAVER_BRAND_CARD_SELECTOR = "div._fe_view_power_content[data-template-id='ugcItem']"

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


def print_line(label: str, value: str):
    print(f"  ▸ {label}\t{value}")


# ==============================
# NAVER: 파워링크
# ==============================


def find_naver_powerlink_rank(driver):
    results = []
    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_POWERLINK_CARD_SELECTOR)

    for idx, card in enumerate(cards, start=1):
        text = card.text.lower()
        if any(kw.lower() in text for kw in NAVER_TARGET_KEYWORDS):
            results.append({"section": "powerlink", "rank": idx})

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
                if any(kw.lower() in card.text.lower() for kw in NAVER_TARGET_KEYWORDS):
                    results.append({"section": "brand", "rank": idx})
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

        if any(kw.lower() in text for kw in NAVER_TARGET_KEYWORDS):
            results.append({"section": section, "rank": rank})

    return results


# ==============================
# NAVER: 인기글 영역
# ==============================


def detect_naver_popular_block(driver):
    blocks = driver.find_elements(By.CSS_SELECTOR, "div[id^='fdr-']")

    for block in blocks:
        try:
            footer = block.find_element(By.TAG_NAME, "footer")
            subject = footer.find_element(
                By.CSS_SELECTOR, "span.fds-comps-footer-more-subject"
            )
            if subject.text.strip() == "인기글":
                return block
        except Exception:
            continue

    return None


def parse_naver_popular_block(block):
    result = {"ads": [], "blogs": [], "cafes": []}
    items = block.find_elements(By.CSS_SELECTOR, "div[data-template-id='ugcItem']")
    ad_rank = 0

    for item in items:
        html = item.get_attribute("outerHTML").lower()
        text = item.text.lower()

        if "_fe_view_power_content" in html or "ader.naver.com" in html:
            ad_rank += 1
            result["ads"].append({"rank": ad_rank})
            continue

        if not any(kw.lower() in text for kw in NAVER_TARGET_KEYWORDS):
            continue

        try:
            url = item.find_elements(By.CSS_SELECTOR, "a[href]")[-1].get_attribute(
                "href"
            )
        except Exception:
            continue

        if "m.blog.naver.com" in url:
            result["blogs"].append({"url": url})
        elif "m.cafe.naver.com" in url:
            result["cafes"].append({"url": url})

    return result


# ==============================
# NAVER: 타이틀 없는 UGC
# ==============================


def has_naver_search_ugc_block(driver) -> bool:
    blocks = driver.find_elements(
        By.CSS_SELECTOR,
        "div.spw_fsolid[data-collection='urB_coR']",
    )
    return len(blocks) > 0


# ==============================
# Elasticsearch
# ==============================

es = Elasticsearch("http://192.168.0.185:9200")


def es_bulk_index(index: str, documents: list) -> int:
    if not documents:
        return 0

    actions = []
    for doc in documents:
        actions.append(
            {
                "_index": index,
                "_source": doc,
            }
        )

    success, _ = helpers.bulk(es, actions)
    return success


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

            # 파워링크
            for r in find_naver_powerlink_rank(crawler.driver):
                bulk_docs.append(
                    {
                        "source": "naver",
                        "query": keyword,
                        "section": r["section"],
                        "rank": r["rank"],
                        "@timestamp": ts,
                    }
                )

            # 브랜드
            for r in find_naver_brand_content_rank(crawler.driver):
                bulk_docs.append(
                    {
                        "source": "naver",
                        "query": keyword,
                        "section": r["section"],
                        "rank": r["rank"],
                        "@timestamp": ts,
                    }
                )

            # 플레이스
            if has_naver_place_block(crawler.driver):
                for r in find_naver_place_rank(crawler.driver):
                    bulk_docs.append(
                        {
                            "source": "naver",
                            "query": keyword,
                            "section": r["section"],
                            "rank": r["rank"],
                            "@timestamp": ts,
                        }
                    )

            # 인기글
            popular_block = detect_naver_popular_block(crawler.driver)
            if popular_block:
                popular = parse_naver_popular_block(popular_block)

                for ad in popular["ads"]:
                    bulk_docs.append(
                        {
                            "source": "naver",
                            "query": keyword,
                            "section": "popular_ad",
                            "rank": ad["rank"],
                            "@timestamp": ts,
                        }
                    )

                for b in popular["blogs"]:
                    bulk_docs.append(
                        {
                            "source": "naver",
                            "query": keyword,
                            "section": "popular_blog",
                            "rank": None,
                            "url": b["url"],
                            "@timestamp": ts,
                        }
                    )

                for c in popular["cafes"]:
                    bulk_docs.append(
                        {
                            "source": "naver",
                            "query": keyword,
                            "section": "popular_cafe",
                            "rank": None,
                            "url": c["url"],
                            "@timestamp": ts,
                        }
                    )

            else:
                if has_naver_search_ugc_block(crawler.driver):
                    bulk_docs.append(
                        {
                            "source": "naver",
                            "query": keyword,
                            "section": "search_ugc",
                            "rank": None,
                            "@timestamp": ts,
                        }
                    )

            if bulk_docs:
                es_bulk_index(index_name, bulk_docs)

    finally:
        crawler.close()


if __name__ == "__main__":
    main()
