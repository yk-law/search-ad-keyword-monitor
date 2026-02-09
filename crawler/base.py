from selenium import webdriver

# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class BaseCrawler:
    """
    NAVER 전용 크롤러
    (snap chromium + Selenium Manager + headless 서버 안정화 최종본)
    """

    def __init__(self):
        options = Options()

        # 🔴 [변경] chromium 실행 파일 (snap 경로)
        options.binary_location = "/snap/bin/chromium"

        # 🔴 [필수] headless 서버 안정화 옵션
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")

        # 🔴 [핵심 추가] DevTools 포트 강제 지정 (없으면 DevToolsActivePort 에러 발생)
        options.add_argument("--remote-debugging-port=9222")

        # 기타 안정화 옵션
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1200,900")

        # 🔴 [변경] chromedriver 직접 지정 ❌ → Selenium Manager 사용
        service = Service()

        self.driver = webdriver.Chrome(
            service=service,
            options=options,
        )

    def open(self, url: str):
        self.driver.get(url)

    def close(self):
        self.driver.quit()


# def create_google_driver():
#     options = webdriver.ChromeOptions()

#     options.add_argument("--headless")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--window-size=1200,900")
#     options.add_argument("--disable-blink-features=AutomationControlled")

#     return webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=options,
#     )
