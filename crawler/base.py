from selenium import webdriver

# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


class BaseCrawler:
    """
    NAVER 전용 크롤러
    (snap chromium + Selenium Manager 최종본)
    """

    def __init__(self):
        options = Options()

        # [변경] apt chromium 경로 → snap chromium 경로
        options.binary_location = "/snap/bin/chromium"

        # 서버 필수 옵션
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1200,900")

        # [변경] chromedriver 경로 지정 제거
        service = Service()  # Selenium Manager 사용

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
