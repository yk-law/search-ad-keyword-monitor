# 광고주/브랜드 식별 키워드
TARGET_KEYWORDS = [
    "YK",
    "법무법인YK",
    "법무법인 YK",
    "yk",
    "법무법인yk",
    "법무법인 yk",
]

# 네이버 DOM 셀렉터 (모바일)
# 모바일 파워링크 (카드 단위)
NAVER_MOBILE_POWERLINK_SELECTOR = "ul[id^='power_link'] > li"
# 브랜드 콘텐츠 카드 (앵커 바로 아래 카드)
NAVER_MOBILE_BRAND_CONTENT_CARD_SELECTOR = (
    "div._fe_view_power_content[data-template-id='ugcItem']"
)
NAVER_MOBILE_RESULT_BLOCK_SELECTOR = "div[id^='fdr-']"
