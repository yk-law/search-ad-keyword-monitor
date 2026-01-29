from selenium.webdriver.common.by import By
from config.constants import (
    TARGET_KEYWORDS,
    NAVER_MOBILE_POWERLINK_SELECTOR,
    NAVER_MOBILE_CARD_SELECTOR,
    NAVER_MOBILE_PLACE_ROOT_SELECTOR,
    NAVER_MOBILE_PLACE_AD_BADGE_SELECTOR,
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
    results = []

    # 브랜드 콘텐츠가 포함된 결과 블록만 찾음
    blocks = driver.find_elements(By.CSS_SELECTOR, NAVER_MOBILE_RESULT_BLOCK_SELECTOR)

    for block in blocks:
        if "브랜드 콘텐츠" not in block.text:
            continue

        cards = block.find_elements(By.CSS_SELECTOR, NAVER_MOBILE_CARD_SELECTOR)

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

        break  # 브랜드 콘텐츠 블록은 하나뿐

    return results


def find_mobile_place_ranks(driver):
    """
    강남형사전문변호사 _ 네이버 검색.html 기준
    - 플레이스 광고
    - 플레이스 자연노출
    UI 노출 순서 기준으로 계산
    """
    results = []
    ad_rank = 0
    organic_rank = 0

    blocks = driver.find_elements(By.CSS_SELECTOR, NAVER_MOBILE_RESULT_BLOCK_SELECTOR)

    for block in blocks:
        # 1️⃣ 이 블록이 플레이스 블록인지 판별
        has_place_badge = block.find_elements(
            By.CSS_SELECTOR, NAVER_MOBILE_PLACE_AD_BADGE_SELECTOR
        )

        if not has_place_badge:
            continue  # ❗ 플레이스 블록 아님 → 스킵

        # 2️⃣ 플레이스 카드만 처리
        cards = block.find_elements(By.CSS_SELECTOR, NAVER_MOBILE_CARD_SELECTOR)

        for card in cards:
            card_text = card.text.lower()

            is_ad = bool(
                card.find_elements(
                    By.CSS_SELECTOR, NAVER_MOBILE_PLACE_AD_BADGE_SELECTOR
                )
            )

            if is_ad:
                ad_rank += 1
                for keyword in TARGET_KEYWORDS:
                    if keyword.lower() in card_text:
                        results.append(
                            {
                                "area": "place",
                                "type": "ad",
                                "rank": ad_rank,
                                "matched_keyword": keyword,
                            }
                        )
                        break
            else:
                organic_rank += 1
                for keyword in TARGET_KEYWORDS:
                    if keyword.lower() in card_text:
                        results.append(
                            {
                                "area": "place",
                                "type": "organic",
                                "rank": organic_rank,
                                "matched_keyword": keyword,
                            }
                        )
                        break

        break  # ✅ 플레이스 블록은 하나뿐

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
