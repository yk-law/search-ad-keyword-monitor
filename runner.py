import json
import time
import random
import string
import urllib.parse
from pathlib import Path

from crawler.base import BaseCrawler
from crawler.naver_mobile import (
    find_mobile_powerlink_rank,
    find_mobile_brand_content_rank,
    find_mobile_search_result_rank,
)


def load_keywords() -> list[str]:
    config_dir = Path(__file__).parent / "config"
    keywords_file = config_dir / "keywords.json"

    with open(keywords_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["keywords"]


# def generate_run_key() -> str:
# return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def build_mobile_search_url(keyword: str) -> str:
    return (
        "https://m.search.naver.com/search.naver"
        f"?query={urllib.parse.quote(keyword)}"
    )


def main(limit: int | None = None):
    crawler = BaseCrawler()
    keywords = load_keywords()

    for idx, keyword in enumerate(keywords, start=1):
        # run_key = generate_run_key()
        # print(f"[{idx}] keyword='{keyword}', run_key={run_key}")

        url = build_mobile_search_url(keyword)
        crawler.open(url)

        time.sleep(random.uniform(3.0, 5.0))

        # 파워링크 순위 확인
        powerlink_rank = find_mobile_powerlink_rank(crawler.driver)
        if powerlink_rank:
            for item in powerlink_rank:
                print(
                    f"[{idx}] keyword='{keyword}'"
                    f"  ✅ 모바일 파워링크 "
                    f"{item['rank']}번째 노출 "
                    f"(matching_keyword='{item['matched_keyword']}') "
                )
        else:
            print("  ❌ 모바일 파워링크 노출 없음")

        # 브랜드 콘텐츠 순위 확인
        brand_ranks = find_mobile_brand_content_rank(crawler.driver)
        if brand_ranks:
            for item in brand_ranks:
                print(
                    f"[{idx}] keyword='{keyword}'"
                    f"  ✅ 브랜드 콘텐츠 "
                    f"{item['rank']}번째 노출 "
                    f"(matching_keyword='{item['matched_keyword']}') "
                )
        else:
            print("  ❌ 브랜드 콘텐츠 노출 없음")

        # 검색 결과 전체 기준 순위 확인
        search_ranks = find_mobile_search_result_rank(crawler.driver)

        if search_ranks:
            for item in search_ranks:
                print(
                    f"[{idx}] keyword='{keyword}' "
                    f"✅ 검색결과 {item['rank']}번째 노출 "
                    f"(matching_keyword='{item['matched_keyword']}')"
                )
        else:
            print(f"[{idx}] keyword='{keyword}' " f"❌ 검색결과 노출 없음")

        if limit and idx >= limit:
            break

    crawler.close()


if __name__ == "__main__":
    # 테스트 용도로 최대 10개 키워드만 처리
    main(limit=10)
