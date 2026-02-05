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
    append_results_to_google_sheet,
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

from config.constants import (
    ES_HOST,
    ES_INDEX_PREFIX,
    BATCH_SIZE,
    GOOGLE_SPREADSHEET_ID,
    GOOGLE_SHEET_NAMES,
    GOOGLE_OUTPUT_SHEET_MAP,
)

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
    index_name = f"{ES_INDEX_PREFIX}-{datetime.now():%Y-%m-%d}"

    # 드라이버 분리 (정답 구조)
    naver_crawler = BaseCrawler()  # snap chromium
    # google_driver = create_google_driver()  # system chrome

    try:
        for sheet_name in GOOGLE_SHEET_NAMES:
            keywords = load_keywords_by_google_sheet(
                spreadsheet_id=GOOGLE_SPREADSHEET_ID,
                sheet_name=sheet_name,
            )
            output_sheet_name = GOOGLE_OUTPUT_SHEET_MAP.get(
                sheet_name, f"results_{sheet_name}"
            )

            batch_summaries = []

            for idx, keyword in enumerate(keywords, start=1):
                print(f"[{sheet_name}][{idx}] keyword='{keyword}'")

                start_t = time.time()
                bulk_docs = []

                # NAVER 크롤링
                try:
                    bulk_docs.extend(run_naver(naver_crawler.driver, keyword))
                except Exception as e:
                    print(f"[NAVER ERROR] keyword='{keyword}' reason={e}")

                elapsed_sec = round(time.time() - start_t, 2)

                if not bulk_docs:
                    continue

                if args.test:
                    print(
                        f"[ES MOCK] index={index_name}\n"
                        f"{json.dumps(bulk_docs, ensure_ascii=False, indent=2)}"
                    )
                    continue

                index_to_es(index_name, bulk_docs)

                # Google Sheets 결과 저장 (시트별로 분리)
                rows = []
                for item in bulk_docs:
                    ts = item.get("@timestamp")
                    ts_str = (
                        datetime.fromisoformat(ts)
                        .astimezone()
                        .strftime("%Y-%m-%d %H:%M:%S")
                        if ts
                        else ""
                    )
                    rows.append(
                        [
                            ts_str,
                            elapsed_sec,
                            keyword,
                            item.get("source"),
                            item.get("section"),
                            item.get("rank"),
                            item.get("title"),
                            item.get("url"),
                        ]
                    )

                append_results_to_google_sheet(
                    spreadsheet_id=GOOGLE_SPREADSHEET_ID,
                    sheet_name=output_sheet_name,
                    rows=rows,
                )

                summary = get_unexposed_summary(keyword, bulk_docs)
                batch_summaries.append(summary)

                if len(batch_summaries) >= BATCH_SIZE or idx == len(keywords):
                    combined_message = "\n".join(batch_summaries)
                    payload = {
                        "event_type": "키워드검색결과",
                        "message": f"[{sheet_name}]\n{combined_message}",
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
