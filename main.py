import warnings
import time, random, json, argparse, subprocess

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from datetime import datetime, timezone

from crawler.base import BaseCrawler

# from crawler.base import create_google_driver
from util import (
    load_keywords,
    load_keywords_by_google_sheet,
    # append_results_to_google_sheet,
    build_naver_mobile_search_url,
    now_utc_iso,
    get_unexposed_summary,
)

from crawler.naver_mobile import (
    ensure_naver_exact_query,
    find_naver_powerlink_rank,
    find_naver_brand_content_rank,
    has_naver_place_block,
    find_naver_place_rank,
    find_popular_content_ocr,
)

# from crawler.google_desktop import (
#     submit_google_search,
#     find_google_results,
# )

from config.constants import ES_HOST, BATCH_SIZE, SPREADSHEET_ID

warnings.filterwarnings("ignore", message=".*pin_memory.*")

es = Elasticsearch(ES_HOST)


# ==============================
# argparse / ES
# ==============================
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--test",
        action="store_true",
        help="ES 인덱싱 없이 로그로만 출력",
    )
    return parser.parse_args()


def index_to_es(index_name: str, docs: list[dict]):
    actions = [{"_index": index_name, "_source": doc} for doc in docs]
    bulk(es, actions)
    print(f"[ES INDEX] index={index_name}, docs={len(docs)}")


# ==============================
# NAVER
# ==============================
def run_naver(driver, keyword: str):
    ts = now_utc_iso()
    docs = []

    driver.get(build_naver_mobile_search_url(keyword))
    time.sleep(random.uniform(4.0, 6.0))

    # 제안 검색어 블록이 있으면 원래 키워드로 전환
    if ensure_naver_exact_query(driver, keyword):
        time.sleep(random.uniform(1.5, 2.5))

    for r in find_naver_powerlink_rank(driver):
        r.update({"source": "naver", "query": keyword, "@timestamp": ts})
        docs.append(r)

    for r in find_naver_brand_content_rank(driver):
        r.update({"source": "naver", "query": keyword, "@timestamp": ts})
        docs.append(r)

    if has_naver_place_block(driver):
        for r in find_naver_place_rank(driver):
            r.update({"source": "naver", "query": keyword, "@timestamp": ts})
            docs.append(r)

    for r in find_popular_content_ocr(driver):
        r.update({"source": "naver", "query": keyword, "@timestamp": ts})
        docs.append(r)

    return docs


# ==============================
# GOOGLE
# ==============================
# def run_google(driver, keyword: str):
#     ts = now_utc_iso()
#     docs = []

#     driver.get("https://www.google.com/?hl=ko")
#     submit_google_search(driver, keyword)

#     for r in find_google_results(driver):
#         r.update(
#             {
#                 "source": "google",
#                 "query": keyword,
#                 "@timestamp": ts,
#             }
#         )
#         docs.append(r)

#     return docs


# ==============================
# main
# ==============================
def main():
    args = parse_args()

    # keywords = load_keywords()
    keywords = load_keywords_by_google_sheet(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name="지역키",
    )

    # run_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    index_name = f"search_ad_keyword_monitoring-{datetime.now(timezone.utc):%Y-%m-%d}"

    # 드라이버 분리 (정답 구조)
    naver_crawler = BaseCrawler()  # snap chromium
    # google_driver = create_google_driver()  # system chrome
    batch_summaries = []

    try:
        for idx, keyword in enumerate(keywords, start=1):
            print(f"[{idx}] keyword='{keyword}'")

            bulk_docs = []

            # NAVER 크롤링
            try:
                bulk_docs.extend(run_naver(naver_crawler.driver, keyword))
            except Exception as e:
                print(f"[NAVER ERROR] keyword='{keyword}' reason={e}")

            # GOOGLE
            # try:
            #     bulk_docs.extend(run_google(google_driver, keyword))
            # except Exception as e:
            #     print(f"[GOOGLE ERROR] keyword='{keyword}' reason={e}")
            #     # Google은 이 구조에서는 재생성까지 필요 없음
            #     continue

            if not bulk_docs:
                continue

            # --test arg 일 경우 ES 인덱싱 없이 출력만 수행
            if args.test:
                print(
                    f"[ES MOCK] index={index_name}\n"
                    f"{json.dumps(bulk_docs, ensure_ascii=False, indent=2)}"
                )
                continue

            # ES 인덱싱
            index_to_es(index_name, bulk_docs)

            # Google Sheets 결과 저장
            # rows = []
            # for item in bulk_docs:
            #     rows.append(
            #         [
            #             run_at,
            #             keyword,
            #             item.get("source"),
            #             item.get("section"),
            #             item.get("rank"),
            #             item.get("title"),
            #             item.get("url"),
            #         ]
            #     )

            # append_results_to_google_sheet(
            #     spreadsheet_id=SPREADSHEET_ID,
            #     sheet_name="results",
            #     rows=rows,
            # )

            # 네이버 웍스 알림 전송
            summary = get_unexposed_summary(keyword, bulk_docs)
            batch_summaries.append(summary)

            if len(batch_summaries) >= BATCH_SIZE or idx == len(keywords):
                combined_message = "\n".join(batch_summaries)
                payload = {
                    "event_type": "키워드검색결과",
                    "message": combined_message,
                }

                subprocess.run(
                    [
                        "curl",
                        "-s",
                        "-X",
                        "POST",
                        "http://localhost:10002/send-event-noti",
                        "-H",
                        "Content-Type: application/json",
                        "-d",
                        json.dumps(payload, ensure_ascii=False),
                    ],
                    check=True,
                )

                print()
                batch_summaries = []

    finally:
        try:
            naver_crawler.close()
        except Exception:
            pass

        # try:
        #     google_driver.quit()
        # except Exception:
        #     pass


if __name__ == "__main__":
    main()
