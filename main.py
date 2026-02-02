import time, random, json, argparse

from crawler.base import BaseCrawler
from selenium.webdriver.common.by import By
from datetime import datetime, timezone
from logo_detector import YKLogoDetector

from util import (
    load_keywords,
    build_naver_mobile_search_url,
    now_utc_iso,
)

from crawler.naver_mobile import (
    find_naver_powerlink_rank,
    find_naver_brand_content_rank,
    has_naver_place_block,
    find_naver_place_rank,
    find_popular_content,
)

# ==============================
# argparse / ES
# ==============================


def parse_args():  # [CHANGED]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="ES 인덱싱 없이 로그로만 출력",
    )
    return parser.parse_args()


def index_to_es(index_name: str, docs: list[dict]):  # [CHANGED]
    """
    실제 환경에서는 Elasticsearch bulk indexing 수행
    """
    print(f"[ES INDEX] index={index_name}, docs={len(docs)}")


# ==============================
# main
# ==============================


def main():
    args = parse_args()

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
                if args.test:  # [CHANGED]
                    print(
                        f"[ES MOCK] index={index_name}\n"
                        f"{json.dumps(bulk_docs, ensure_ascii=False, indent=2)}"
                    )
                else:
                    index_to_es(index_name, bulk_docs)

    finally:
        crawler.close()


if __name__ == "__main__":
    main()
