import urllib.parse, json, time
from datetime import datetime, timezone
from pathlib import Path
from selenium.webdriver.common.by import By
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def load_keywords():
    with open("config/keywords.json", encoding="utf-8") as f:
        return json.load(f)["keywords"]


# ==============================
# GOOGLE SHEETS
# ==============================
def load_keywords_by_google_sheet(
    spreadsheet_id: str,
    sheet_name: str,
):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    credentials = Credentials.from_service_account_file(
        "config/google_service_account.json",
        scopes=SCOPES,
    )

    service = build("sheets", "v4", credentials=credentials)

    result = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A2:A",
        )
        .execute()
    )

    rows = result.get("values", [])

    keywords = [row[0].strip() for row in rows if row and row[0].strip()]

    return keywords


def append_results_to_google_sheet(
    spreadsheet_id: str,
    rows: list[list],
    sheet_name: str = "results",
):
    """
    Google Sheets의 results 시트에 row 단위로 append 한다.
    """
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    credentials = Credentials.from_service_account_file(
        "config/google_service_account.json",
        scopes=SCOPES,
    )

    service = build("sheets", "v4", credentials=credentials)

    for attempt in range(1, 6):
        try:
            service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A1",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body={"values": rows},
            ).execute()
            break
        except HttpError as e:
            if e.resp.status in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2**attempt)
                continue
            raise


# ==============================
# NAVER
# ==============================
def build_naver_mobile_search_url(keyword: str) -> str:
    return "https://m.search.naver.com/search.naver?query=" + urllib.parse.quote(
        keyword
    )


def now_utc_iso():
    return datetime.now(timezone.utc).isoformat()


def save_element_screenshot(element, path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    element.screenshot(path)


def get_thumbnail_element_from_card(card):
    try:
        return card.find_element(
            By.CSS_SELECTOR,
            "div[data-sds-comp='RectangleImage']:not(.sds-comps-image-circle) img",
        )
    except Exception:
        return None


def get_card_url(card):
    try:
        a = card.find_element(By.CSS_SELECTOR, "a[data-heatmap-target='.link'][href]")
        return a.get_attribute("href")
    except Exception:
        pass

    try:
        a = card.find_element(By.CSS_SELECTOR, "a[href*='?art=']")
        return a.get_attribute("href")
    except Exception:
        pass

    try:
        a = card.find_element(By.CSS_SELECTOR, "a[href]")
        return a.get_attribute("href")
    except Exception:
        return None


def is_brand_content(card) -> bool:
    try:
        card.find_element(By.CSS_SELECTOR, "a[href*='ader.naver.com']")
        return True
    except Exception:
        pass

    cls = card.get_attribute("class") or ""
    return "_fe_view_power_content" in cls


def resolve_ugc_content_type(url: str) -> str:
    if not url:
        return url
    if "m.cafe.naver.com" in url:
        return "카페"
    if "m.blog.naver.com" in url:
        return "블로그"
    return url


def is_kin_content(url: str) -> bool:
    if not url:
        return False
    return "m.kin.naver.com" in url or "kin.naver.com" in url


def get_unexposed_summary(keyword, bulk_docs):
    now_str = datetime.now().strftime("%m-%d %H:%M")

    # 전체 영역 목록
    all_sections = {
        "파워링크",
        "브랜드콘텐츠",
        "플레이스_광고",
        "플레이스_일반",
        "인기글",
    }

    # 노출된 영역 수집
    exposed_sections = set()
    for item in bulk_docs:
        section = item.get("section", "")
        if section:
            exposed_sections.add(section)

    # 미노출 영역 계산
    unexposed = all_sections - exposed_sections

    # 미노출 영역 문자열 생성
    if unexposed:
        unexposed_str = ", ".join(sorted(unexposed))
    else:
        unexposed_str = "없음"

    return f"{now_str} | {keyword} | 미노출영역: {unexposed_str}"
