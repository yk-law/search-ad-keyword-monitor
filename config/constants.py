import datetime

# ==============================
# ElasticSearch 설정
# ==============================
ES_HOST = "http://localhost:9200"
ES_INDEX_PREFIX = "search_ad_keyword_monitoring"
BATCH_SIZE = 10

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
# GOOGLE SHEETS
# ==============================
GOOGLE_SPREADSHEET_ID = "15pWYWNvk42DqlrBwK4k3v0Teq5QIK6e15RgWz6OPOus"
GOOGLE_SHEET_NAMES = [
    "전국지사키",
    "지역키",
    "집중키",
    "전쟁키",
]
GOOGLE_OUTPUT_SHEET_MAP = {
    "전국지사키": "전국지사키_RESULT",
    "지역키": "지역키_RESULT",
    "집중키": "집중키_RESULT",
    "전쟁키": "전쟁키_RESULT",
}
