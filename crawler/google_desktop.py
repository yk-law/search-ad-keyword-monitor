import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# ==============================
# Google 검색 입력창 찾기
# ==============================
def find_google_search_input(driver, timeout=10):
    """
    Google 첫 진입 시 consent(동의) 화면을 처리하고
    검색 입력창(textarea[name='q'])을 반환한다.
    """
    wait = WebDriverWait(driver, timeout)

    # 1. consent(동의) 화면 처리
    try:
        agree_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[.//text()[contains(., '동의') "
                    "or contains(., 'Agree') "
                    "or contains(., 'Accept')]]",
                )
            )
        )
        agree_btn.click()
        time.sleep(1)
    except TimeoutException:
        # 동의 화면이 없으면 정상
        pass

    # 2. 검색 입력창 찾기 (Google 최신 DOM 기준)
    try:
        return wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='q']"))
        )
    except TimeoutException:
        raise RuntimeError("Google 검색 입력창을 찾지 못했습니다.")


# ==============================
# Google 검색 수행
# ==============================
def submit_google_search(driver, keyword, timeout=10):
    """
    Google 검색을 수행하고
    - 검색 결과 페이지
    - CAPTCHA 페이지
    중 하나가 나타날 때까지 대기한다.
    """
    search_input = find_google_search_input(driver, timeout=timeout)

    search_input.clear()
    search_input.send_keys(keyword)
    search_input.send_keys(Keys.ENTER)

    # 검색 결과 OR CAPTCHA 페이지 대기
    WebDriverWait(driver, timeout).until(
        lambda d: (
            d.find_elements(By.CSS_SELECTOR, "div#search")
            or "sorry" in d.current_url
            or d.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
        )
    )

    # CAPTCHA 감지
    if "sorry" in driver.current_url:
        raise RuntimeError("Google CAPTCHA detected")


# ==============================
# Google 검색 결과 파싱
# ==============================
def find_google_results(driver):
    """
    Google desktop 검색 결과를 파싱하여
    AD / SEO 결과를 반환한다.

    NOTE:
    - rank는 '수집 순서 기준'
    - 실제 화면 노출 순서와 100% 일치하지 않을 수 있음
    """
    results = []
    rank = 1

    # CAPTCHA 페이지면 바로 skip
    if "sorry" in driver.current_url:
        print("[GOOGLE] CAPTCHA page detected, skip results")
        return results

    # 검색 결과 영역 대기
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div#search"))
    )

    # ======================
    # 광고 영역
    # ======================
    for ad_id in ("tads", "tadsb", "bottomads"):
        ads = driver.find_elements(
            By.CSS_SELECTOR,
            f"div#{ad_id} h3, div#{ad_id} [role='heading']",
        )
        for el in ads:
            text = el.text.strip()
            if not text:
                continue

            results.append(
                {
                    "type": "AD",
                    "rank": rank,
                    "title": text,
                }
            )
            rank += 1

    # ======================
    # SEO 영역
    # ======================
    seo_titles = driver.find_elements(
        By.CSS_SELECTOR,
        "div#rso h3, div#rso [role='heading']",
    )
    for el in seo_titles:
        text = el.text.strip()
        if not text:
            continue

        results.append(
            {
                "type": "SEO",
                "rank": rank,
                "title": text,
            }
        )
        rank += 1

    return results
