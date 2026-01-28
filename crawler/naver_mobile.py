from selenium.webdriver.common.by import By
from config.constants import (
    TARGET_KEYWORDS,
    NAVER_MOBILE_POWERLINK_SELECTOR,
    NAVER_MOBILE_BRAND_CONTENT_CARD_SELECTOR,
    NAVER_MOBILE_RESULT_BLOCK_SELECTOR,
)


def find_mobile_powerlink_rank(driver) -> list[dict]:
    """
    모바일 네이버 PowerLink 광고 카드(li) 기준으로
    TARGET_KEYWORDS가 몇 번째 광고인지 반환
    """
    results = []

    cards = driver.find_elements(By.CSS_SELECTOR, NAVER_MOBILE_POWERLINK_SELECTOR)

    for idx, card in enumerate(cards, start=1):
        card_text = card.text.lower()

        for keyword in TARGET_KEYWORDS:
            if keyword.lower() in card_text:
                results.append(
                    {
                        "rank": idx,
                        "matched_keyword": keyword,
                    }
                )
                break

    return results


def find_mobile_brand_content_rank(driver) -> list[dict]:
    """
    모바일 네이버 브랜드 콘텐츠(ugcItem) 카드 기준으로
    TARGET_KEYWORDS가 몇 번째인지 반환
    """
    results = []

    cards = driver.find_elements(
        By.CSS_SELECTOR, NAVER_MOBILE_BRAND_CONTENT_CARD_SELECTOR
    )

    for idx, card in enumerate(cards, start=1):
        card_text = card.text.lower()

        for keyword in TARGET_KEYWORDS:
            if keyword in card_text:
                results.append(
                    {
                        "rank": idx,
                        "matched_keyword": keyword,
                    }
                )
                break

    return results


def find_mobile_search_result_rank(driver) -> list[dict]:
    """
    모바일 네이버 검색 결과 기준으로
    이미지 영역을 제외한 결과만 카운트하여
    TARGET_KEYWORDS 노출 순위를 반환
    """
    results = []
    visible_rank = 0

    blocks = driver.find_elements(
        By.CSS_SELECTOR,
        NAVER_MOBILE_RESULT_BLOCK_SELECTOR,
    )

    for block in blocks:
        # 이미지 영역 제외
        block_id = block.get_attribute("data-block-id") or ""
        meta_area = block.get_attribute("data-meta-area") or ""

        if "image" in block_id or meta_area == "image":
            continue

        visible_rank += 1
        block_text = block.text.lower()

        for keyword in TARGET_KEYWORDS:
            if keyword.lower() in block_text:
                results.append(
                    {
                        "rank": visible_rank,
                        "matched_keyword": keyword,
                    }
                )
                break

    return results
