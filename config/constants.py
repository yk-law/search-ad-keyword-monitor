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
# 카드
NAVER_MOBILE_CARD_SELECTOR = "div._fe_view_power_content[data-template-id='ugcItem']"
# 플레이스 전체 루트
NAVER_MOBILE_PLACE_ROOT_SELECTOR = "#place-app-root"
# 광고 배지가 있는 카드 내부 요소
NAVER_MOBILE_PLACE_AD_BADGE_SELECTOR = "span.place_blind"

# 검색 결과 블록 (이미지 영역 제외)
NAVER_MOBILE_RESULT_BLOCK_SELECTOR = "div[id^='fdr-']"
